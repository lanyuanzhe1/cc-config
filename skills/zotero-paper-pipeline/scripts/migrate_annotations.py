#!/usr/bin/env python3
"""把重译好的 PDF 挂到 Zotero 条目下，迁移旧译文上的批注，再删除旧附件。

用法:
  python3 migrate_annotations.py NEW.pdf REMAP.json PARENT_KEY OLD_ATTACHMENT_KEY "Full Text PDF (中文翻译)"

REMAP.json 由 remap_annotations.py 生成（rects 为 PyMuPDF 左上原点）。
本脚本负责把 y 翻转成 PDF 原生坐标（Zotero 的 annotationPosition 用左下原点！
y' = 页高 - y），否则批注会在 PDF 里上下镜像错位。

前置：Docker 里 pdftranslate 已重译好并压到 <20MB（Zotero 单附件上传上限），
      由 shell 完成（见 SKILL.md）。
"""
import importlib.util, json, os, hashlib, time, urllib.parse, urllib.request, urllib.error, shutil, sys
import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("zotero", os.path.join(os.path.dirname(os.path.abspath(__file__)), "zotero.py"))
zt = importlib.util.module_from_spec(spec); spec.loader.exec_module(zt)

PDF, REMAP, PARENT, OLD, TITLE = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
doc = pymupdf.open(PDF)
heights = {i: doc[i].rect.height for i in range(doc.page_count)}
mapping = {o["key"]: o for o in json.load(open(REMAP))}

st, body = zt.call("GET", f"/users/0/items/{OLD}/children?itemType=annotation")
anns = json.loads(body)
print("annotations on old attachment:", len(anns))

b = open(PDF, "rb").read()
md5 = hashlib.md5(b).hexdigest(); mtime = int(os.path.getmtime(PDF) * 1000)
print("file:", round(len(b) / 1e6, 1), "MB  md5:", md5[:10])

st, body = zt.call("POST", "/users/0/items", [{
    "itemType": "attachment", "linkMode": "imported_file", "contentType": "application/pdf",
    "title": TITLE, "filename": os.path.basename(PDF), "parentItem": PARENT, "libraryID": 1}])
assert st == 200, (st, body[:300])
NEW = json.loads(body)["successful"]["0"]["key"]
print("NEW attachment:", NEW)

form = urllib.parse.urlencode({"md5": md5, "filename": os.path.basename(PDF), "filesize": len(b),
                               "mtime": mtime, "contentType": "application/pdf"}).encode()
info = None
for _ in range(8):
    st, body = zt.call("POST", f"/users/0/items/{NEW}/file", raw=form,
                       ctype="application/x-www-form-urlencoded", headers={"If-None-Match": "*"})
    if st == 200:
        info = json.loads(body); break
    time.sleep(2)
assert info, "upload authorize failed (Zotero 本地 API 是否在跑？)"
for _ in range(8):
    try:
        r = urllib.request.urlopen(urllib.request.Request(info["url"], data=b, method="POST",
                                   headers={"Content-Type": "application/pdf"}), timeout=180)
        if r.status in (200, 201): break
    except urllib.error.HTTPError as e:
        print("bytes POST err:", e.code); time.sleep(2)
else:
    raise SystemExit("bytes upload failed")
zt.call("POST", f"/users/0/items/{NEW}/file",
        raw=urllib.parse.urlencode({"upload": info["uploadKey"]}).encode(),
        ctype="application/x-www-form-urlencoded")
st, body = zt.call("GET", f"/users/0/items/{NEW}")
print("uploaded:", json.loads(body)["data"].get("filename"))

ok = 0
for a in anns:
    k = a["key"]; m = mapping.get(k)
    if not m or not m["rects"]:
        print("  NO MAPPING for", k); continue
    p = m["page"]; H = heights[p]
    flipped = [[round(x0, 3), round(H - y1, 3), round(x1, 3), round(H - y0, 3)] for x0, y0, x1, y1 in m["rects"]]
    st2, b2 = zt.call("PATCH", f"/users/0/items/{k}", body={
        "parentItem": NEW,
        "annotationPosition": json.dumps({"pageIndex": p, "rects": flipped}),
        "annotationPageLabel": str(p + 1)},
        headers={"If-Unmodified-Since-Version": str(a["version"])})
    print(f"  {k} -> p{p+1} HTTP {st2} :: {m['matched'][:50]}")
    ok += st2 in (200, 204)
print(f"moved {ok}/{len(anns)}")
if ok != len(anns):
    raise SystemExit("abort: incomplete move, 旧附件保留")

st, body = zt.call("GET", f"/users/0/items/{NEW}/children?itemType=annotation")
print("annotations on new:", len(json.loads(body)))

st, body = zt.call("GET", f"/users/0/items/{OLD}")
ver = json.loads(body)["version"]
st, b2 = zt.call("DELETE", f"/users/0/items/{OLD}", headers={"If-Unmodified-Since-Version": str(ver)})
print("DELETE old attachment:", st)
od = os.path.expanduser(f"~/Zotero/storage/{OLD}")
if os.path.isdir(od):
    shutil.rmtree(od); print("removed", od)

st, body = zt.call("GET", f"/users/0/items/{PARENT}/children")
for i in json.loads(body):
    print(" child:", i["key"], i["data"].get("itemType"), "|", i["data"].get("title"))
print("NEW_KEY", NEW)

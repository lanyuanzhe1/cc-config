#!/usr/bin/env python3
"""把旧译文上的 Zotero 批注重新锚定到新译文的同一句话上。

用法:
  python3 remap_annotations.py NEW.pdf OLD_ANNOTATIONS.json OUT.json

输入 OLD_ANNOTATIONS.json 是旧批注列表（至少含 key / text / pageIndex / rects），
可从 Zotero API `/users/0/items/<附件key>/children?itemType=annotation` 导出。
输出 OUT.json 的 rects 是 **PyMuPDF 左上原点**坐标，写回 Zotero 前必须翻转 y
（见 migrate_annotations.py）。

原理：新译文措辞和老译文不同，但段落位置由原 PDF 的版面决定，所以用批注文本
在新 PDF 的译文列里做模糊匹配（窗口相似度 + 连续匹配块合并），再按行生成 rects。
匹配率低的批注用 MANUAL 里的短语强制指定。
"""
import pymupdf, json, re, difflib, sys

PDF = sys.argv[1]
SRC = sys.argv[2]
OUT = sys.argv[3]

# 自动匹配不准时手工指定锚定短语，例如 {"XXXX": ["令牌高效代码接口", "代码接口"]}
MANUAL = {}

anns = json.load(open(SRC))
COLUMN_X = 610  # 双栏版式：译文在右半页（x >= 610）

def is_word(ch): return bool(re.match(r"[\u4e00-\u9fffA-Za-z0-9]", ch))
def nmap(s):
    out, idx = [], []
    for i, ch in enumerate(s):
        if is_word(ch): out.append(ch.lower()); idx.append(i)
    return "".join(out), idx

doc = pymupdf.open(PDF)
pages = []
for p in range(doc.page_count):
    chars = []
    for b in doc[p].get_text("rawdict").get("blocks", []):
        for l in b.get("lines", []):
            if abs(l.get("dir", (1, 0))[1]) > 0.2:   # 跳过旋转水印
                continue
            for s in l.get("spans", []):
                for c in s.get("chars", []):
                    x0, y0, x1, y1 = c["bbox"]
                    if x0 >= COLUMN_X:
                        chars.append((x0, y0, x1, y1, c["c"]))
    chars.sort(key=lambda t: (round(t[1], 1), t[0]))
    n, idx = nmap("".join(c[4] for c in chars))
    pages.append((n, idx, chars))

PUNCT = set("。，；：！？、,.!?;:()（）[]【】“”\"' ")

def expand(chars, i0, i1, maxn=8):
    a, b = i0, i1
    for _ in range(maxn):
        if a > 0 and chars[a - 1][4] not in PUNCT and chars[a - 1][4].isprintable():
            a -= 1
        else: break
    for _ in range(maxn):
        if b < len(chars) and chars[b][4] not in PUNCT and chars[b][4].isprintable():
            b += 1
        else: break
    return a, b

def chain_span(sn, pn, st, wlen):
    rs, re_ = max(0, st - 60), min(len(pn), st + wlen + 60)
    blocks = [b for b in difflib.SequenceMatcher(None, sn, pn[rs:re_]).get_matching_blocks() if b.size >= 2]
    if not blocks: return st, st + wlen
    chains, cur = [], [blocks[0]]
    for b in blocks[1:]:
        pa = cur[-1]
        if b.a - (pa.a + pa.size) <= 6 and b.b - (pa.b + pa.size) <= 6: cur.append(b)
        else: chains.append(cur); cur = [b]
    chains.append(cur)
    best = max(chains, key=lambda c: sum(x.size for x in c))
    return rs + best[0].b, rs + best[-1].b + best[-1].size

def rects_for(chars, a, b):
    lines = {}
    for i in range(a, b):
        x0, y0, x1, y1, c = chars[i]
        if not c.strip(): continue
        k = round((y0 + y1) / 2, 0)
        if k not in lines: lines[k] = [x0, y0, x1, y1]
        else:
            L = lines[k]; L[0] = min(L[0], x0); L[1] = min(L[1], y0)
            L[2] = max(L[2], x1); L[3] = max(L[3], y1)
    return [[round(v, 3) for v in lines[k]] for k in sorted(lines)]

out = []
for a in anns:
    sn, _ = nmap(a["text"])
    best = None
    for p, (pn, idx, chars) in enumerate(pages):
        if len(pn) < 4: continue
        s2 = {sn[i:i+2] for i in range(len(sn) - 1)}
        p2 = {pn[i:i+2] for i in range(len(pn) - 1)}
        if len(s2 & p2) < max(2, len(s2) // 3): continue
        for wlen in range(max(4, len(sn) - 10), len(sn) + 13):
            for st in range(0, max(0, len(pn) - wlen + 1)):
                r = difflib.SequenceMatcher(None, sn, pn[st:st + wlen]).ratio()
                if best is None or r > best[0]: best = (r, p, st, wlen)
    if best is None:
        out.append(dict(key=a["key"], page=0, ratio=0.0, rects=[], matched="", note="NO_MATCH"))
        continue
    r, p, st, wlen = best
    pn, idx, chars = pages[p]
    cs, ce = chain_span(sn, pn, st, wlen)
    a0, a1 = idx[cs], idx[ce - 1] + 1
    if r < 0.85: a0, a1 = expand(chars, a0, a1, 8)
    out.append(dict(key=a["key"], page=p, ratio=round(r, 3), rects=rects_for(chars, a0, a1),
                    matched="".join(chars[i][4] for i in range(a0, a1)), note="fuzzy"))

for o in out:
    if o["key"] in MANUAL:
        seq_by_page = ["".join(c[4] for c in chars) for _, _, chars in pages]
        for ph in MANUAL[o["key"]]:
            hit = next(((p, s.find(ph)) for p, s in enumerate(seq_by_page) if ph in s), None)
            if hit:
                p, j = hit
                chars = pages[p][2]
                o.update(page=p, ratio=1.0, rects=rects_for(chars, j, j + len(ph)),
                         matched=ph, note="manual:" + ph)
                break

json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
for o in out:
    print(f"{o['key']} p{o['page']+1} r={o['ratio']} rects={len(o['rects'])} [{o.get('note')}] :: {o['matched'][:60]}")

#!/usr/bin/env python3
"""Zotero local-API helper: add items (arXiv/DOI), upload PDFs, attach files.

Usage:
  python3 zotero.py collections
  python3 zotero.py add-arxiv 2502.14907 --collection "LLM&agent" [--no-pdf]
  python3 zotero.py add-doi 10.1038/s41566-026-01889-0 --collection 太赫兹
  python3 zotero.py attach <ITEM_KEY> <FILE> [--title "Full Text PDF (中文翻译)"]
  python3 zotero.py upload <ATTACHMENT_KEY> <FILE>
"""
import argparse, hashlib, json, os, re, shutil, sqlite3, sys, tempfile, time
import urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

ZOTERO = os.path.expanduser("~/Zotero")
SQLITE = os.path.join(ZOTERO, "zotero.sqlite")
API = "http://127.0.0.1:23119/api"
UA = {"User-Agent": "Mozilla/5.0 (zotero-paper-pipeline)"}


# ---------------------------------------------------------------- auth
def read_setting(key):
    tmp = os.path.join(tempfile.mkdtemp(), "z.sqlite")
    shutil.copyfile(SQLITE, tmp)  # DB is locked while Zotero runs
    try:
        con = sqlite3.connect(tmp)
        setting, k = key.split("|", 1)
        row = con.execute("SELECT value FROM settings WHERE setting=? AND key=?", (setting, k)).fetchone()
        return row[0] if row else None
    finally:
        shutil.rmtree(os.path.dirname(tmp), ignore_errors=True)


def get_sid():
    sid = read_setting("localAPI|serverID")
    if not sid:
        sys.exit("localAPI|serverID not found — enable Zotero Settings > Advanced > Allow other applications")
    return sid


CACHE = os.path.expanduser("~/.cache/zotero-paper-pipeline/key")


def _key_ok(sid, key):
    req = urllib.request.Request(API + "/users/0/items?limit=1",
                                 headers={"Zotero-Server-ID": sid, "Zotero-API-Key": key})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception:
        return False


def get_key(sid):
    # A granted key is remembered by Zotero; reuse it (authorize can block on a GUI prompt)
    if os.path.exists(CACHE):
        key = open(CACHE).read().strip()
        if key and _key_ok(sid, key):
            return key
    body = json.dumps({"appName": "dsh"}).encode()
    req = urllib.request.Request(API + "/local/authorize", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Zotero-Server-ID": sid})
    try:
        key = json.loads(urllib.request.urlopen(req, timeout=120).read())["key"]
    except urllib.error.HTTPError as e:
        sys.exit(f"authorize failed {e.code}: {e.read()[:200]}")
    except Exception as e:
        sys.exit(f"authorize failed ({e}) — approve the Zotero dialog, or put an existing key in {CACHE}")
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    open(CACHE, "w").write(key)
    return key


SID = get_sid()
KEY = get_key(SID)


def call(method, path, body=None, raw=None, ctype="application/json", headers=None, timeout=180):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"Zotero-Server-ID": SID, "Zotero-API-Key": KEY}
    if data is not None:
        h["Content-Type"] = ctype
    if headers:
        h.update(headers)
    req = urllib.request.Request(API + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


# ---------------------------------------------------------------- metadata
def arxiv_meta(aid):
    u = f"https://export.arxiv.org/api/query?id_list={aid}"
    xml = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode()
    ns = {"a": "http://www.w3.org/2005/Atom"}
    e = ET.fromstring(xml).find("a:entry", ns)
    pdf = None
    for link in e.findall("a:link", ns):
        if link.get("title") == "pdf":
            pdf = link.get("href").replace("http://", "https://")
    return {
        "title": " ".join(e.find("a:title", ns).text.split()),
        "abstract": " ".join(e.find("a:summary", ns).text.split()),
        "date": e.find("a:published", ns).text[:10],
        "authors": [" ".join(a.find("a:name", ns).text.split()) for a in e.findall("a:author", ns)],
        "pdf": pdf,
        "id": aid,
    }


def crossref_meta(doi):
    u = f"https://api.crossref.org/works/{doi}"
    m = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read())["message"]
    ab = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.get("abstract", ""))).strip()
    return {
        "title": (m.get("title") or [""])[0].replace("\u2009", " "),
        "abstract": ab,
        "date": "-".join(str(x) for x in (m.get("published") or m.get("issued"))["date-parts"][0]),
        "authors": [((a.get("given", "") + " " + a.get("family", "")).strip()) for a in m.get("author", [])],
        "journal": (m.get("container-title") or [""])[0],
        "volume": m.get("volume", ""), "issue": m.get("issue", ""), "page": m.get("page", ""),
        "doi": m["DOI"],
    }


def creators(names):
    out = []
    for n in names:
        parts = n.split()
        if len(parts) == 1:
            out.append({"creatorType": "author", "name": n})
        else:
            out.append({"creatorType": "author", "firstName": " ".join(parts[:-1]), "lastName": parts[-1]})
    return out


def collection_key(name_or_key):
    st, body = call("GET", "/users/0/collections?limit=200")
    cols = json.loads(body)
    for c in cols:
        if name_or_key in (c["key"], c["data"]["name"]):
            return c["key"]
    sys.exit(f"collection not found: {name_or_key}\n" + "\n".join(f'  {c["key"]}  {c["data"]["name"]}' for c in cols))


# ---------------------------------------------------------------- items
def create_item(item):
    st, body = call("POST", "/users/0/items", [item])
    if st != 200:
        sys.exit(f"create failed {st}: {body[:300]}")
    return json.loads(body)["successful"]["0"]["key"]


def add_pdf(parent, path, title="Full Text PDF"):
    b = open(path, "rb").read()
    md5 = hashlib.md5(b).hexdigest()
    st, body = call("POST", "/users/0/items",
                    [{"itemType": "attachment", "linkMode": "imported_file", "contentType": "application/pdf",
                      "title": title, "filename": os.path.basename(path), "parentItem": parent, "libraryID": 1}])
    if st != 200:
        sys.exit(f"attachment item failed {st}: {body[:300]}")
    key = json.loads(body)["successful"]["0"]["key"]
    upload(key, path)
    return key


def upload(key, path, retries=4):
    """Three-phase local API upload: authorize -> bytes -> register.

    The local server occasionally answers 404 'No endpoint found' for the byte
    POST (routing hiccup on large bodies) and 412 when a stale synced hash is
    recorded without the file on disk. Both are retried.
    """
    b = open(path, "rb").read()
    md5 = hashlib.md5(b).hexdigest()
    mtime = int(os.path.getmtime(path) * 1000)
    disk = os.path.expanduser(f"~/Zotero/storage/{key}")
    for attempt in range(retries):
        form = urllib.parse.urlencode({"md5": md5, "filename": os.path.basename(path),
                                       "filesize": len(b), "mtime": mtime,
                                       "contentType": "application/pdf"}).encode()
        st, body = call("POST", f"/users/0/items/{key}/file", raw=form,
                        ctype="application/x-www-form-urlencoded", headers={"If-None-Match": "*"})
        if st == 412:  # server thinks the file exists
            if os.path.isdir(disk) and os.listdir(disk):
                return
            st, body = call("POST", "/users/0/items", [{"itemType": "attachment", "linkMode": "imported_file",
                            "contentType": "application/pdf", "title": "Full Text PDF",
                            "filename": os.path.basename(path),
                            "parentItem": json.loads(call("GET", f"/users/0/items/{key}")[1])["data"]["parentItem"],
                            "libraryID": 1}])
            key = json.loads(body)["successful"]["0"]["key"]
            st, body = call("POST", f"/users/0/items/{key}/file", raw=form,
                            ctype="application/x-www-form-urlencoded", headers={"If-None-Match": "*"})
        if st != 200:
            print(f"  upload authorize {st} ({body[:80]!r}), retrying")
            time.sleep(2)
            continue
        info = json.loads(body)
        if info.get("exists"):
            return
        st2, b2 = call("POST", info["url"], raw=b, ctype="application/pdf")
        if st2 not in (200, 201):
            print(f"  upload bytes {st2} ({b2[:80]!r}), retrying")
            time.sleep(2)
            continue
        reg = urllib.parse.urlencode({"upload": info["uploadKey"]}).encode()
        st3, b3 = call("POST", f"/users/0/items/{key}/file", raw=reg,
                       ctype="application/x-www-form-urlencoded", headers={"If-None-Match": "*"})
        if st3 == 204:
            return
        print(f"  upload register {st3} ({b3[:80]!r}), retrying")
        time.sleep(2)
    sys.exit("upload failed after retries")


def find_dupe(title):
    q = urllib.parse.quote(title.split(":")[0][:60])
    st, body = call("GET", f"/users/0/items?q={q}&limit=10")
    if st != 200:
        return None
    for it in json.loads(body):
        if it["data"].get("title", "").lower()[:40] == title.lower()[:40]:
            return it["key"]
    return None


# ---------------------------------------------------------------- commands
def cmd_collections(args):
    st, body = call("GET", "/users/0/collections?limit=200")
    for c in json.loads(body):
        print(f'{c["key"]}  {c["data"]["name"]}')


def _finish(key, item_title, pdf_path, col):
    print(f"item {key}  {item_title}")
    if pdf_path:
        print(f"attachment {add_pdf(key, pdf_path)}")


def cmd_add_arxiv(args):
    m = arxiv_meta(args.arxiv)
    pdf = None
    if not args.no_pdf:
        pdf = f"/tmp/{args.arxiv}.pdf"
        urllib.request.urlretrieve(m["pdf"], pdf)
    extra = f"arXiv: {m['id']}"
    if args.venue:
        # e.g. --venue "ICLR 2026" --venue-full "International Conference on Learning Representations (ICLR) 2026"
        extra += f"\nAccepted at {args.venue}"
        if args.openreview:
            extra += f"\nOpenReview: {args.openreview}"
    if args.venue:
        item = {"itemType": "conferencePaper", "title": m["title"], "creators": creators(m["authors"]),
                "abstractNote": m["abstract"], "date": args.year or m["date"][:4],
                "conferenceName": args.venue,
                "proceedingsTitle": args.venue_full or args.venue,
                "place": args.place or "", "archiveID": f"arXiv:{m['id']}",
                "url": args.openreview or f"https://arxiv.org/abs/{m['id']}",
                "extra": extra, "libraryID": 1,
                "collections": [collection_key(args.collection)] if args.collection else [],
                "tags": [{"tag": args.venue}], "language": "en"}
    else:
        item = {"itemType": "preprint", "title": m["title"], "creators": creators(m["authors"]),
                "abstractNote": m["abstract"], "date": m["date"], "repository": "arXiv",
                "archiveID": f"arXiv:{m['id']}", "url": f"https://arxiv.org/abs/{m['id']}",
                "DOI": f"10.48550/arXiv.{m['id']}", "libraryID": 1,
                "collections": [collection_key(args.collection)] if args.collection else [],
                "language": "en"}
    dupe = find_dupe(m["title"])
    if dupe:
        item_key = dupe
        print(f"duplicate found, reusing {dupe}")
    else:
        item_key = create_item(item)
    _finish(item_key, m["title"], pdf, args.collection)


def cmd_add_doi(args):
    m = crossref_meta(args.doi)
    item = {"itemType": "journalArticle", "title": m["title"], "creators": creators(m["authors"]),
            "abstractNote": m["abstract"], "date": m["date"], "publicationTitle": m["journal"],
            "volume": m["volume"], "issue": m["issue"], "pages": m["page"], "DOI": m["doi"],
            "url": "https://doi.org/" + m["doi"], "libraryID": 1,
            "collections": [collection_key(args.collection)] if args.collection else []}
    dupe = find_dupe(m["title"])
    key = dupe or create_item(item)
    _finish(key, m["title"], args.pdf, args.collection)


def cmd_attach(args):
    print(f"attachment {add_pdf(args.item, args.file, args.title)}")


def cmd_upload(args):
    upload(args.key, args.file)
    print("ok")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("collections"); s.set_defaults(func=cmd_collections)

    s = sub.add_parser("add-arxiv"); s.add_argument("arxiv"); s.add_argument("--collection")
    s.add_argument("--venue", help="e.g. 'ICLR 2026' → creates a conferencePaper")
    s.add_argument("--venue-full", help="full proceedings title")
    s.add_argument("--place"); s.add_argument("--year")
    s.add_argument("--openreview", help="OpenReview forum URL, used as item URL")
    s.add_argument("--no-pdf", action="store_true"); s.set_defaults(func=cmd_add_arxiv)

    s = sub.add_parser("add-doi"); s.add_argument("doi"); s.add_argument("--collection")
    s.add_argument("--pdf"); s.set_defaults(func=cmd_add_doi)

    s = sub.add_parser("attach"); s.add_argument("item"); s.add_argument("file")
    s.add_argument("--title", default="Full Text PDF"); s.set_defaults(func=cmd_attach)

    s = sub.add_parser("upload"); s.add_argument("key"); s.add_argument("file")
    s.set_defaults(func=cmd_upload)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

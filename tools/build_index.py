#!/usr/bin/env python3
"""
Keeps the site self-maintaining. Run from the repo root:

    python3 tools/build_index.py

1. Any HTML in folder/ that still carries base64-embedded images gets them
   extracted to <name>_img/ as lossless WebP. Page logic is untouched:
   BOOK.images holds URLs instead of data: URIs, and both readers assign
   to an <img> src.
2. apps.json gains an entry for every HTML in folder/ that lacks one, and
   loses entries whose local file is gone. Existing entries are left alone,
   so hand-edited names and descriptions survive.

Per-file overrides, if you want them, go in the HTML's <head>:
    <meta name="app-name"        content="CP Precast">
    <meta name="app-category"    content="precast">
    <meta name="app-description" content="Only for informational purpose.">
"""
import base64, io, json, os, re, sys

SITE    = "https://skiptheroutine.github.io"
APPS    = "apps.json"
SRC_DIR = "folder"
DEFAULT_DESC = "Only for informational purpose."

# filename keyword -> category id in apps.json
CATEGORY_RULES = [
    ("precast",     "precast"),
    ("field-model", "steel"),
    ("steel",       "steel"),
    ("calc",        "engineering"),
]
FALLBACK_CATEGORY = "tools"


# ---------- 1. image extraction ----------

def meta(html, name):
    m = re.search(r'<meta\s+name=["\']%s["\']\s+content=["\'](.*?)["\']' % name,
                  html, re.I)
    return m.group(1).strip() if m else None


def extract_images(path):
    """Pull base64 images out of a part-book page. Returns bytes saved."""
    html = open(path, encoding="utf-8").read()
    m = re.search(r"^const BOOK = (\{.*\});?$", html, re.M)
    if not m:
        return 0
    try:
        book = json.loads(m.group(1))
    except json.JSONDecodeError:
        print(f"  ! {path}: BOOK is not valid JSON, skipping", file=sys.stderr)
        return 0

    imgs = book.get("images") or []
    if not imgs or not str(imgs[0]).startswith("data:"):
        return 0   # already extracted, or nothing to do

    from PIL import Image   # imported late so apps.json-only runs need no Pillow

    stem   = os.path.splitext(os.path.basename(path))[0]
    outdir = os.path.join(os.path.dirname(path), stem + "_img")
    os.makedirs(outdir, exist_ok=True)

    before = os.path.getsize(path)
    urls = []
    for i, uri in enumerate(imgs):
        raw = base64.b64decode(uri.split(",", 1)[1])
        buf = io.BytesIO()
        Image.open(io.BytesIO(raw)).save(
            buf, "WEBP", lossless=True, quality=100, method=4)
        name = f"{i:04d}.webp"
        with open(os.path.join(outdir, name), "wb") as fh:
            fh.write(buf.getvalue())
        urls.append(f"{stem}_img/{name}")

    book["images"] = urls
    new = "const BOOK = " + json.dumps(book, separators=(",", ":")) + ";"
    open(path, "w", encoding="utf-8").write(html[:m.start()] + new + html[m.end():])

    after = os.path.getsize(path)
    print(f"  extracted {len(urls)} images from {os.path.basename(path)}: "
          f"{before/1e6:.1f} MB -> {after/1e6:.2f} MB")
    return before - after


# ---------- 2. apps.json ----------

def derive(path):
    html = open(path, encoding="utf-8", errors="replace").read(8192)
    stem = os.path.splitext(os.path.basename(path))[0]

    name = meta(html, "app-name") or stem.replace("-", " ").replace("_", " ").title()
    cat  = meta(html, "app-category")
    if not cat:
        low = stem.lower()
        cat = next((c for kw, c in CATEGORY_RULES if kw in low), FALLBACK_CATEGORY)
    desc = meta(html, "app-description") or DEFAULT_DESC
    return {"name": name, "category": cat,
            "url": f"{SITE}/{SRC_DIR}/{os.path.basename(path)}",
            "description": desc}


def local_path(url):
    """Repo-relative path for one of our own URLs, else None."""
    if not url.startswith(SITE + "/"):
        return None
    return url[len(SITE) + 1:].split("?")[0].split("#")[0]


def sync_apps():
    data  = json.load(open(APPS, encoding="utf-8"))
    apps  = data.get("apps", [])
    valid = {c["id"] for c in data.get("categories", [])}
    changed = False

    # drop entries whose local file is gone (external URLs are left alone)
    kept = []
    for a in apps:
        p = local_path(a.get("url", ""))
        if p and not os.path.exists(p):
            print(f"  removed dead entry: {a.get('name')} -> {p}")
            changed = True
        else:
            kept.append(a)
    apps = kept

    known = {local_path(a.get("url", "")) for a in apps}
    for fn in sorted(os.listdir(SRC_DIR)):
        if not fn.lower().endswith(".html"):
            continue
        rel = f"{SRC_DIR}/{fn}"
        if rel in known:
            continue
        entry = derive(rel)
        if entry["category"] not in valid:
            entry["category"] = FALLBACK_CATEGORY
        apps.append(entry)
        print(f"  added: {entry['name']}  [{entry['category']}]  {rel}")
        changed = True

    if changed:
        data["apps"] = apps
        with open(APPS, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    return changed


def main():
    if not os.path.isdir(SRC_DIR):
        sys.exit(f"no {SRC_DIR}/ directory here - run from the repo root")
    print("checking for embedded images...")
    for fn in sorted(os.listdir(SRC_DIR)):
        if fn.lower().endswith(".html"):
            extract_images(os.path.join(SRC_DIR, fn))
    print("syncing apps.json...")
    if not sync_apps():
        print("  apps.json already up to date")
    print("done")


if __name__ == "__main__":
    main()

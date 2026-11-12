#!/usr/bin/env python3
"""Index four openly licensed, machine-readable frontend sources at pinned versions.

  * Google Fonts family metadata   https://fonts.google.com/metadata/fonts      (fonts: OFL / Apache / UFL)
  * Three.js official examples     mrdoob/three.js examples/files.json           (MIT)
  * Lucide icons                   lucide-static <version> tags.json             (ISC)
  * Tabler icons                   @tabler/icons <version> icons.json            (MIT)

Only names, categories, tags and links are stored. No font files, icon files or example
code are copied into the repository; previews link to the upstream files at the pinned
version. Python standard library only.

    python3 scripts/collect-open-sources.py
"""
import json
import re
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UA = {"User-Agent": "Frontend-Library-reference-index/1.0"}
TODAY = date.today().isoformat()


def get(url, accept=None):
    headers = dict(UA)
    if accept:
        headers["Accept"] = accept
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
        return r.read().decode("utf-8"), r.geturl()


def get_json(url, accept=None):
    text, final = get(url, accept)
    return json.loads(text), final


def esc(s):
    return str(s or "").replace("|", "\\|").replace("\n", " ").strip()


def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.rstrip() + "\n")


def save(name, payload):
    payload["count"] = len(payload["items"])
    # compact: these catalogs are large and are fetched by the website
    (DATA / name).write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{name}: {payload['count']:,}")


def header(title, blurb, source, count, back="../../README.md"):
    return (f"<div align=\"center\">\n\n# {title}\n\n{blurb}\n\n"
            f"<sub><b>{count:,}</b> entries · collected <b>{TODAY}</b> from <a href=\"{source}\">{source}</a> · "
            f"<a href=\"{back}\">← Back to library</a> · <a href=\"https://frontendlibrary.vercel.app/library/\">Search them on the website</a></sub>\n\n</div>\n\n")


# ───────────────────────────────────────────────────────── Google Fonts
def google_fonts():
    src = "https://fonts.google.com/metadata/fonts"
    meta, _ = get_json(src)
    items = []
    for f in meta["familyMetadataList"]:
        fam = f["family"]
        styles = sorted(f.get("fonts", {}))
        axes = [a.get("tag") for a in f.get("axes", []) if a.get("tag")]
        tags = [f.get("category", "").lower()] + (["variable"] if axes else []) + (["noto"] if f.get("isNoto") else [])
        items.append({
            "name": fam,
            "url": f"https://fonts.google.com/specimen/{quote_plus(fam)}",
            "source": src,
            "collected": TODAY,
            "category": f.get("category", ""),
            "designers": f.get("designers", [])[:4],
            "styles": len(styles),
            "axes": axes,
            "subsets": [s for s in f.get("subsets", []) if s != "menu"][:8],
            "dateAdded": f.get("dateAdded", ""),
            "popularity": f.get("popularity"),
            "cssUrl": f"https://fonts.googleapis.com/css2?family={quote_plus(fam)}&display=swap",
            "license": "Open-source font licence (OFL, Apache 2.0 or UFL — see the family page)",
            "tags": [t for t in tags if t],
        })
    items.sort(key=lambda x: (x["popularity"] or 99999, x["name"]))
    save("google-fonts.json", {"source": "https://fonts.google.com/", "collected": TODAY,
         "license": "Fonts are open source; licence varies per family (OFL, Apache 2.0, UFL).", "items": items})

    by = defaultdict(list)
    for x in items:
        by[x["category"] or "Other"].append(x)
    out = header("🔤 Google Fonts", "Every open-source family on Google Fonts, ordered by popularity, with designers, styles and variable axes. Free for commercial use under each family's licence.", "https://fonts.google.com/", len(items))
    out += "> [!TIP]\n> Each family has a ready `cssUrl` in [`data/google-fonts.json`](../../data/google-fonts.json). Pair one display face with one text face.\n\n"
    out += "| Category | Families |\n|:--|--:|\n" + "".join(f"| [{c}](#{re.sub('[^a-z0-9]+', '-', c.lower()).strip('-')}) | {len(v)} |\n" for c, v in sorted(by.items(), key=lambda kv: -len(kv[1]))) + "\n"
    for c, rows in sorted(by.items(), key=lambda kv: -len(kv[1])):
        out += f"## {c}\n\n| # | Family | Designer | Styles | Variable axes |\n|--:|:--|:--|--:|:--|\n"
        for i, x in enumerate(rows, 1):
            out += f"| {i} | [{esc(x['name'])}]({x['url']}) | {esc(', '.join(x['designers'][:2]))} | {x['styles']} | {esc(' '.join(x['axes'])) or '—'} |\n"
        out += "\n"
    write("fonts/google-fonts/README.md", out)
    return src


# ───────────────────────────────────────────────────────── Three.js examples
def pretty(slug):
    parts = slug.split("_")
    rest = " ".join(parts[1:]).replace("-", " ").strip()
    return (rest[:1].upper() + rest[1:]) if rest else parts[0].title()


def threejs():
    commit, _ = get_json("https://api.github.com/repos/mrdoob/three.js/commits/dev", "application/vnd.github+json")
    sha = commit["sha"]
    src = f"https://github.com/mrdoob/three.js/blob/{sha}/examples/files.json"
    files, _ = get_json(f"https://raw.githubusercontent.com/mrdoob/three.js/{sha}/examples/files.json")
    tagmap, _ = get_json(f"https://raw.githubusercontent.com/mrdoob/three.js/{sha}/examples/tags.json")
    items = []
    for group, names in files.items():
        for n in names:
            items.append({
                "id": n,
                "name": pretty(n),
                "url": f"https://threejs.org/examples/#{n}",
                "source": src,
                "collected": TODAY,
                "category": group,
                "kind": "webgpu-example" if group.startswith("webgpu") else "webgl-example",
                "tags": [group.split(" / ")[0]] + tagmap.get(n, [])[:6],
                "preview": f"https://threejs.org/examples/screenshots/{n}.jpg",
                "code": f"https://github.com/mrdoob/three.js/blob/{sha}/examples/{n}.html",
                "license": "MIT (three.js)",
                "attribution": "three.js authors",
            })
    save("threejs-examples.json", {"source": "https://threejs.org/examples/", "collected": TODAY, "commit": sha,
         "license": "MIT", "items": items})
    by = defaultdict(list)
    for x in items:
        by[x["category"]].append(x)
    out = header("🧊 Three.js examples", f"All official three.js examples (WebGL, WebGPU, WebXR, physics, post-processing) with live demos and source pinned to commit `{sha[:10]}`.", "https://threejs.org/examples/", len(items))
    out += "| Group | Examples |\n|:--|--:|\n" + "".join(f"| {g} | {len(v)} |\n" for g, v in by.items()) + "\n"
    for g, rows in by.items():
        out += f"## {g}\n\n| Example | Live demo | Source |\n|:--|:--|:--|\n"
        for x in rows:
            out += f"| {esc(x['name'])} | [open]({x['url']}) | [html]({x['code']}) |\n"
        out += "\n"
    write("animations/threejs-examples/README.md", out)
    return src


# ───────────────────────────────────────────────────────── Icons
def icons():
    _, lu_final = get("https://unpkg.com/lucide-static@latest/package.json")
    lu_ver = re.search(r"lucide-static@([^/]+)/", lu_final).group(1)
    _, tb_final = get("https://unpkg.com/@tabler/icons@latest/package.json")
    tb_ver = re.search(r"icons@([^/]+)/", tb_final).group(1)
    lu_src = f"https://unpkg.com/lucide-static@{lu_ver}/tags.json"
    tb_src = f"https://unpkg.com/@tabler/icons@{tb_ver}/icons.json"
    lucide, _ = get_json(lu_src)
    tabler, _ = get_json(tb_src)
    items = []
    for name, tags in lucide.items():
        items.append({"name": name, "set": "Lucide", "url": f"https://lucide.dev/icons/{name}", "source": lu_src,
                      "category": "Lucide", "tags": tags[:6], "svg": f"https://unpkg.com/lucide-static@{lu_ver}/icons/{name}.svg"})
    for name, x in tabler.items():
        style = "outline" if "outline" in x.get("styles", {}) else next(iter(x.get("styles", {"filled": 0})))
        items.append({"name": name, "set": "Tabler", "url": f"https://tabler.io/icons/icon/{name}", "source": tb_src,
                      "category": x.get("category") or "Uncategorised", "tags": [str(t) for t in x.get("tags", [])][:6],
                      "styles": sorted(x.get("styles", {})), "svg": f"https://unpkg.com/@tabler/icons@{tb_ver}/icons/{style}/{name}.svg"})
    save("open-icons.json", {"source": "https://lucide.dev/ and https://tabler.io/icons", "collected": TODAY,
         "versions": {"lucide-static": lu_ver, "@tabler/icons": tb_ver}, "license": "Lucide: ISC (Lucide contributors) · Tabler: MIT (Paweł Kuna and Tabler contributors)", "items": items})

    lu = [x for x in items if x["set"] == "Lucide"]
    tb = [x for x in items if x["set"] == "Tabler"]
    out = header("✳️ Open icon sets", f"{len(lu):,} Lucide icons (ISC, v{lu_ver}) and {len(tb):,} Tabler icons (MIT, v{tb_ver}) — every name links to its icon page; SVG links are pinned in [`data/open-icons.json`](../../data/open-icons.json).", "https://lucide.dev/", len(items))
    out += "```bash\nnpm i lucide-static        # or lucide-react, lucide-vue-next\nnpm i @tabler/icons        # or @tabler/icons-react\n```\n\n"
    out += f"## Lucide ({len(lu):,})\n\n"
    letters = defaultdict(list)
    for x in lu:
        letters[x["name"][0].upper()].append(x)
    for k in sorted(letters):
        out += f"**{k}** — " + " · ".join(f"[{x['name']}]({x['url']})" for x in letters[k]) + "\n\n"
    out += f"## Tabler ({len(tb):,})\n\n"
    cats = defaultdict(list)
    for x in tb:
        cats[x["category"]].append(x)
    for c in sorted(cats):
        out += f"### {c} ({len(cats[c])})\n\n" + " · ".join(f"[{x['name']}]({x['url']})" for x in cats[c]) + "\n\n"
    write("icons/open-icons/README.md", out)
    return lu_src, tb_src


def policies(sources):
    p = DATA / "source-policies.json"
    data = json.loads(p.read_text())
    known = {s["url"] for s in data["sources"]}
    for s in sources:
        if s["url"] not in known:
            data["sources"].append(s)
    p.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    gf = google_fonts()
    tj = threejs()
    lu, tb = icons()
    policies([
        {"url": "https://fonts.google.com/", "robots": "https://fonts.google.com/robots.txt", "result": "public-metadata-endpoint (robots disallows /license/ only)",
         "capture": f"Family metadata from {gf}; no font files downloaded."},
        {"url": "https://github.com/mrdoob/three.js", "result": "public-git-repository (MIT)", "capture": f"Example index from {tj}; previews/demos link to threejs.org."},
        {"url": "https://lucide.dev/", "result": "public-npm-package (ISC)", "capture": f"Icon names and tags from {lu}; SVGs linked, not copied."},
        {"url": "https://tabler.io/icons", "result": "public-npm-package (MIT)", "capture": f"Icon names, categories and tags from {tb}; SVGs linked, not copied."},
    ])

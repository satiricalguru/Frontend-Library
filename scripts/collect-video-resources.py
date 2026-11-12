#!/usr/bin/env python3
"""Index landing-page asset and motion sources from Brad Traversy's resource list.

The upstream README is fetched at a resolved commit; linked providers and media
are never crawled or downloaded. Python standard library only.
"""
import argparse
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
REPO = "bradtraversy/design-resources-for-developers"
HOME = f"https://github.com/{REPO}"
SECTIONS = {
    "Stock Videos": ("stock-videos", "video-source", ["stock-video", "hero-video", "background-video"]),
    "Stock Music & Sound Effects": ("stock-music--sound-effects", "audio-source", ["audio", "sound-effects"]),
    "Design Inspiration": ("design-inspiration", "inspiration-directory", ["landing-pages", "inspiration"]),
    "Javascript Animation Libraries": ("javascript-animation-libraries", "animation-library", ["javascript", "animation"]),
    "CSS Animations": ("css-animations", "animation-library", ["css", "animation"]),
    "UI Graphics": ("ui-graphics", "visual-resource", ["illustration", "graphics"]),
    "Product & Image Mockups": ("product--image-mockups", "mockup-source", ["mockup", "product-shot"]),
    "Stock Photos": ("stock-photos", "image-source", ["photography", "hero-image"]),
    "Image Compression": ("image-compression", "optimization-tool", ["performance", "image-optimization"]),
}
PURPOSES = {
    "video-source": "Source for selecting landing-page footage; individual clip terms need review.",
    "audio-source": "Source for optional audio; individual tracks, attribution and playback controls need review.",
    "inspiration-directory": "Directory for finding visual references; listed sites are not captured by this entry.",
    "animation-library": "Motion implementation resource; inspect current documentation and licence before adopting.",
    "visual-resource": "Source of visual design resources; inspect the selected asset's format and usage rights.",
    "mockup-source": "Resource for product imagery or presentation mockups; verify asset rights and editability.",
    "image-source": "Source for selecting landing-page photographs; individual image rights need review.",
    "optimization-tool": "Asset preparation resource; inspect its current formats and privacy behavior before use.",
}


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Frontend-Library-reference-index/1.0", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def parse(markdown, commit, collected):
    section = ""
    items = []
    skipped = []
    for line_number, line in enumerate(markdown.splitlines(), 1):
        if line.startswith("## "):
            section = line[3:].strip()
        if section not in SECTIONS or not line.lstrip().startswith("|"):
            continue
        match = re.match(r"^\s*\|\s*\[([^\]]+)\]\((https?://[^\s)]+)\)", line)
        if not match:
            if "](" in line:
                skipped.append({"section": section, "line": line_number, "reason": "Unsupported table-link syntax"})
            continue
        name, url = (html.unescape(value.strip()) for value in match.groups())
        anchor, kind, base_tags = SECTIONS[section]
        tags = list(base_tags)
        # Tags reflect descriptions in the upstream list, not independently verified runtime claims.
        description = line[match.end():].lower()
        for tag, pattern in [("3d", r"\b3d\b"), ("webgl", r"\bwebgl\b"), ("three-js", r"three\.js"),
                             ("scroll", r"scroll"), ("svg", r"\bsvg\b"), ("texture", r"texture"),
                             ("background", r"background"), ("video", r"\bvideo"), ("model", r"\bmodel")]:
            if re.search(pattern, name.lower() + " " + description) and tag not in tags:
                tags.append(tag)
        digest = hashlib.sha256(f"{section}|{name}|{url}".encode()).hexdigest()[:8]
        items.append({
            "id": f"traversy-{slug(section)}-{slug(name)[:55]}-{digest}",
            "name": name,
            "url": url,
            "source": f"{HOME}/blob/{commit}/readme.md#{anchor}",
            "discoverySource": f"{HOME}#{anchor}",
            "collected": collected,
            "category": section,
            "kind": kind,
            "tags": tags,
            "description": PURPOSES[kind],
            "licensingCheckRequired": True,
            "providerVerified": False,
            "evidence": "upstream-link-index",
            "upstreamCommit": commit,
            "upstreamPath": "readme.md",
            "upstreamLine": line_number,
        })
    return items, skipped


def validate(data):
    items = data["items"]
    if data["count"] != len(items) or len({item["id"] for item in items}) != len(items):
        raise ValueError("Count mismatch or duplicate IDs")
    if not all(any(item["category"] == section for item in items) for section in SECTIONS):
        raise ValueError("A selected upstream section was not found; inspect README changes")
    for item in items:
        if not item["name"] or not item["collected"] or not item["licensingCheckRequired"]:
            raise ValueError(f"Incomplete record: {item.get('id')}")
        for field in ("url", "source"):
            parsed = urlparse(item[field])
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError(f"Invalid {field}: {item[field]}")


def render(data, license_text):
    counts = Counter(item["category"] for item in data["items"])
    out = "# Video, visual assets and motion resources\n\n"
    out += f"**{data['count']} indexed resource rows across {len(counts)} categories**, including **{counts['Stock Videos']} stock-video providers**, from [Brad Traversy's design resources]({HOME}#stock-videos). Collected {data['collected']}.\n\n"
    out += "This is a source index for assembling rich landing pages: footage, image assets, motion tools, mockups and visual inspiration. It contains no downloaded stock media, screenshots or recordings of the listed providers. A directory entry is not a captured landing page.\n\n"
    out += f"[Machine-readable catalog](../../data/video-resources.json) · [Immutable upstream README]({data['upstream']['readme']}) · [Library](../../README.md)\n\n"
    out += "## Coverage\n\n| Category | Indexed rows |\n|:--|--:|\n"
    for category in SECTIONS:
        out += f"| [{category}](#{SECTIONS[category][0]}) | {counts[category]} |\n"
    out += "\nCounts describe source rows, not unique providers: one tool can appear in more than one section. The collector records original section, line number and commit for each entry. Linked-provider availability and their current terms have not been independently verified.\n\n"
    out += "## Use media in a landing page\n\n"
    out += "Choose a clip or image only after checking the provider's current licence, attribution, commercial-use and redistribution terms. For video heroes, plan a static poster, muted inline playback, a reduced-motion alternative and accessible playback controls. Measure encoded byte size and mobile decoding cost before choosing full-viewport video. Music and sound need separate rights and a user-controlled playback path.\n\n"
    out += "For a reference recreation, record the original composition, crop, duration and interaction role. A similar stock clip does not guarantee an exact visual match. Keep chosen asset URLs and licence evidence alongside the project's implementation brief.\n\n"
    for category in SECTIONS:
        out += f"## {category}\n\n| Resource | Upstream row | Tags from upstream metadata |\n|:--|:--|:--|\n"
        for item in data["items"]:
            if item["category"] != category:
                continue
            name = item["name"].replace("|", "\\|")
            out += f"| [{name}]({item['url']}) | [line {item['upstreamLine']}]({data['upstream']['readme']}#L{item['upstreamLine']}) | {', '.join(item['tags'])} |\n"
        out += "\n"
    out += "## Refresh and validation\n\n```bash\npython3 scripts/collect-video-resources.py\npython3 scripts/collect-video-resources.py --validate-only\n```\n\n"
    out += "Refresh resolves the upstream default branch to an immutable commit before fetching its README. To reproduce the current snapshot, pass `--commit` with the SHA in the JSON catalog; use `--date` to preserve its collection date. Only the repository metadata, README and licence are requested. Linked providers are not crawled.\n\n"
    out += "## Attribution and licence boundary\n\n"
    out += f"The upstream list is MIT licensed: [licence at the indexed commit]({data['upstream']['licenseUrl']}). That permission applies to the list, not automatically to footage, audio, models, photography, paid tools or other content at its links. All entries therefore carry `licensingCheckRequired: true`. This index uses names, links, category facts and new usage notes instead of copying the upstream promotional descriptions.\n\n"
    out += "<details>\n<summary>Upstream list licence notice</summary>\n\n```text\n" + license_text.strip() + "\n```\n\n</details>\n"
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", help="Immutable upstream commit; default resolves current default branch")
    parser.add_argument("--date", default=datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat())
    parser.add_argument("--validate-only", action="store_true", help="Validate local JSON without networking")
    args = parser.parse_args()
    target = ROOT / "data/video-resources.json"
    if args.validate_only:
        data = json.loads(target.read_text())
        validate(data)
        print(f"ok: {data['count']} attributed resource rows; no stock media bundled")
        return 0
    metadata = json.loads(fetch(f"https://api.github.com/repos/{REPO}"))
    if args.commit:
        if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
            parser.error("--commit must be a full 40-character lowercase SHA")
        commit = args.commit
    else:
        commit = json.loads(fetch(f"https://api.github.com/repos/{REPO}/commits/{metadata['default_branch']}"))["sha"]
    readme_url = f"https://raw.githubusercontent.com/{REPO}/{commit}/readme.md"
    markdown = fetch(readme_url)
    license_url = f"https://raw.githubusercontent.com/{REPO}/{commit}/LICENSE"
    license_text = fetch(license_url)
    if not license_text.startswith("MIT License"):
        raise ValueError("Upstream licence changed; review before regenerating")
    items, skipped = parse(markdown, commit, args.date)
    data = {"version": 1, "source": f"{HOME}#stock-videos", "collected": args.date, "count": len(items),
            "upstream": {"repository": REPO, "defaultBranch": metadata["default_branch"], "commit": commit,
                         "readme": f"{HOME}/blob/{commit}/readme.md", "readmeRaw": readme_url,
                         "license": "MIT", "licenseUrl": license_url,
                         "attribution": "Brad Traversy and design-resources-for-developers contributors"},
            "coverage": {"selectedSections": list(SECTIONS), "countsByCategory": dict(Counter(item["category"] for item in items)),
                         "skippedRows": skipped, "linkedProvidersCrawled": False, "mediaBundled": False,
                         "note": "Indexed rows may repeat a provider in different categories; provider availability and asset terms are unverified."},
            "items": items}
    validate(data)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    readme = ROOT / "images/video-resources/README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text(render(data, license_text))
    print(f"Collected {len(items)} resource rows at {commit}; {len(skipped)} unsupported rows")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, urllib.error.URLError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error

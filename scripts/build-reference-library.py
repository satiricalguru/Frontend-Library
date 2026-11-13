#!/usr/bin/env python3
"""Build the capture index, per-page guides and agent manifest from captured evidence."""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def write(relative, content):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n")


def link_lusion_index(captures):
    """Give each Lusion index entry the screenshot and recording of its own capture package.

    Matches on the exact page URL (desktop captures only; a successful capture wins over one
    that needs review). Entries without a usable capture are left untouched."""
    path = ROOT / "data/lusion.json"
    if not path.exists():
        return
    norm = lambda url: url.rstrip("/").lower()
    rank = {"captured": 0, "needs-review": 1}
    best = {}
    for cap in captures:
        if cap["status"] not in rank or cap.get("viewport", {}).get("mobile") or not cap.get("preview"):
            continue
        key = norm(cap["url"])
        if key not in best or rank[cap["status"]] < rank[best[key]["status"]]:
            best[key] = cap
    data = json.loads(path.read_text())
    for item in data["items"]:
        for field in ("preview", "video", "capture", "captureStatus", "captureGuide"):
            item.pop(field, None)
        cap = best.get(norm(item["url"]))
        if cap:
            # the first frame can catch media that hasn't painted yet; use the most detailed of
            # the first three checkpoints (largest JPEG ≈ most visual detail)
            folder = (ROOT / cap["preview"]).parent
            frames = sorted(folder.glob("checkpoint-0[0-2].jpg"), key=lambda p: p.stat().st_size, reverse=True)
            preview = frames[0].relative_to(ROOT).as_posix() if frames else cap["preview"]
            item.update({"preview": preview, "capture": cap["id"], "captureStatus": cap["status"], "captureGuide": cap["guide"]})
            if cap.get("video"):
                item["video"] = cap["video"]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def build():
    items = []
    for path in sorted((ROOT / "captures").glob("*/*/page.json")):
        record = json.loads(path.read_text())
        base = path.parent.relative_to(ROOT).as_posix()
        initial = record.get("initial", {})
        group = record.get("group") or path.parent.parent.name
        tags = [group, record["kind"], record.get("scroll", {}).get("mode", "unknown") + "-scroll"]
        if initial.get("canvases"):
            tags.append("canvas")
        if record.get("video"):
            tags.append("motion-recording")
        guide = f"docs/reference-library/pages/{record['id']}.md"
        item = {"id": record["id"], "name": record["name"], "url": record["url"], "source": record["source"],
                "kind": record["kind"], "status": record["status"], "capturedAt": record["capturedAt"],
                "viewport": record["viewport"], "tags": tags, "record": f"{base}/page.json", "guide": guide,
                "checkpointCount": len(record.get("checkpoints", [])), "resourceCount": len(record.get("resources", [])),
                "scrollCoverage": record.get("scroll", {}).get("coverage"), "group": group}
        if record.get("preview"):
            item["preview"] = f"{base}/{record['preview']}"
        if record.get("video"):
            item["video"] = f"{base}/{record['video']['file']}"
        items.append(item)
        relative = "../../../"
        out = f"# {record['name']}\n\n[Source]({record['url']}) · [Discovery page]({record['source']}) · [Raw record]({relative}{base}/page.json)\n\n"
        out += f"Captured `{record['capturedAt']}` at **{record['viewport']['width']} × {record['viewport']['height']}**. Type: **{record['kind']}**. Status: **{record['status']}**.\n\n"
        if item.get("video"):
            out += f"[Play/download the recorded browser traversal]({relative}{item['video']}) ({record['video']['durationMs']/1000:.1f} seconds, muted). This is a browser recording, not an extracted source video.\n\n"
        out += "## Visual checkpoints\n\nEach percentage is requested capture progress, not a verified animation timeline. Check the recorded URL and visible section IDs.\n\n"
        for checkpoint in record.get("checkpoints", []):
            out += f"![Checkpoint {checkpoint['frame']} at {checkpoint['elapsedMs']/1000:.1f}s]({relative}{base}/{checkpoint['file']})\n\n"
            out += f"Frame `{checkpoint['frame']}` · `{checkpoint['elapsedMs']/1000:.1f}s` · requested progress `{checkpoint['requestedProgress']}` · [actual route]({checkpoint['state']['url']}).\n\n"
        out += "## Observed structure\n\n| Section ID | Initial y | Height |\n|:--|--:|--:|\n"
        for section in initial.get("sections", []):
            out += f"| `{section['id']}` | {section['rect']['y']} | {section['rect']['height']} |\n"
        out += "\n## Implementation boundary\n\n"
        out += "This package records the route above. A studio case study may show videos of a client website; it does not establish that client's runtime or interactions. Inspect the outbound links in the record before choosing a live project as a target.\n\n"
        for limitation in record.get("limitations", []):
            out += f"- {limitation}\n"
        out += f"\n{record['rights']}\n\n[Agent workflow]({relative}.agents/skills/frontend-library/SKILL.md) · [Implementation guidance]({relative}.agents/skills/frontend-library/references/implementation.md)\n"
        write(guide, out)
    featured = {"lusion-home":0, "lusion-home-mobile":1, "live-ion":2, "lusion-about":3, "lusion-projects":4}
    items.sort(key=lambda item: (0 if item['status']=='captured' else 1, featured.get(item['id'],5), item['name'].lower()))
    catalog = {"version": 1, "source": "https://lusion.co/ and brand homepages discovered via https://styles.refero.design/", "count": len(items), "items": items}
    write("data/landing-pages.json", json.dumps(catalog, indent=2, ensure_ascii=False))
    link_lusion_index(items)
    good = [item for item in items if item["status"] == "captured"]
    videos = sum(bool(item.get("video")) for item in items)
    checkpoints = sum(item["checkpointCount"] for item in items)
    resources = sum(item["resourceCount"] for item in items)
    unique_resources = {resource["url"] for path in (ROOT / "captures").glob("*/*/page.json")
                        for resource in json.loads(path.read_text()).get("resources", [])}
    summary = {"packages": len(items), "captured": len(good), "uniqueRoutes": len({item['url'] for item in items}),
               "videos": videos, "checkpoints": checkpoints, "observedResourceResponses": resources,
               "uniqueResourceUrls": len(unique_resources), "byKind": dict(Counter(item['kind'] for item in items)),
               "byStatus": dict(Counter(item['status'] for item in items))}
    write("data/capture-summary.json", json.dumps(summary, indent=2))
    readme = ROOT / "README.md"
    if readme.exists():
        stats = (f"<!-- capture-stats:start -->\n**{len(items)} evidence packages across {summary['uniqueRoutes']} source routes · "
                 f"{videos} browser recordings · {checkpoints} visual checkpoints · {len(unique_resources)} unique observed resource URLs.**\n\n"
                 f"{len(good)} completed captures · {summary['byStatus'].get('needs-review',0)} need review · {summary['byStatus'].get('failed',0)} failed. "
                 "Packages include desktop/mobile variants and diagnostic captures; [see coverage and limitations](docs/reference-library/README.md).\n<!-- capture-stats:end -->")
        readme.write_text(re.sub(r"<!-- capture-stats:start -->.*?<!-- capture-stats:end -->", lambda _: stats, readme.read_text(), flags=re.S))
    out = "# Landing-page and motion evidence\n\n"
    out += f"**{len(items)} capture packages · {videos} browser recordings · {checkpoints} visual checkpoints · {len(unique_resources)} unique observed resource URLs.**\n\n"
    out += f"Status: **{len(good)} captured**, **{sum(item['status']=='needs-review' for item in items)} need review**, **{sum(item['status']=='failed' for item in items)} failed**. Recordings of failed or incomplete loads are retained as diagnostics and must not be used as working-page evidence.\n\n"
    out += "This collection extends the link catalogs with visual evidence for agents and contributors. It contains landing pages, studio pages, case studies and lab experiments; the type is explicit in every row. It is not an offline mirror or a source-code recovery.\n\n"
    out += "[Open the searchable viewer](../../library/index.html) (serve the repo over HTTP) · [Agent skill](../../.agents/skills/frontend-library/SKILL.md) · [Homepage deep dive](lusion-home.md) · [Capture methodology](methodology.md)\n\n"
    out += "| Page | Type | Status | Checkpoints | Video | Evidence |\n|:--|:--|:--|--:|:--|:--|\n"
    for item in items:
        video = f"[MP4](../../{item['video']})" if item.get("video") else "—"
        out += f"| [{item['name'].replace('|', chr(92)+'|')}]({item['url']}) | {item['kind']} | {item['status']} | {item['checkpointCount']} | {video} | [guide](pages/{item['id']}.md) · [JSON](../../{item['record']}) |\n"
    out += "\n## Refero coverage\n\nThe existing **1,342 Refero styles** remain searchable, with palette/typeface metadata and original links. Their DESIGN.md files, full pages and animations are not bundled here. Refero's AI-crawler restriction prevented a new deep crawl; see [source policies](../../data/source-policies.json). A style index is not a recorded landing page.\n\n"
    out += "## Refresh one page\n\n```bash\nnode scripts/capture-pages.mjs --id lusion-home --force\npython3 scripts/build-reference-library.py\npython3 scripts/validate-references.py\n```\n\nCapture prerequisites: Node 22+, Chrome/Chromium (`CHROME_PATH` on other installations), and ffmpeg. Captures run sequentially using a temporary browser profile. They include requested wheel/pointer input; no forms are submitted. Source media keeps its owner's rights.\n"
    write("docs/reference-library/README.md", out)
    collections = []
    for name, filename in [("styles", "refero-styles.json"), ("lusion", "lusion.json"), ("motion", "motion-examples.json"),
                           ("transitions", "transitions.json"), ("godly", "godly.json"), ("fonts", "envato-award-fonts.json"),
                           ("captures", "landing-pages.json"), ("codrops", "codrops-webgl.json"),
                           ("design-md", "design-md.json"), ("media-resources", "video-resources.json"),
                           ("google-fonts", "google-fonts.json"), ("threejs", "threejs-examples.json"), ("icons", "open-icons.json"), ("showcases", "showcases.json")]:
        if not (ROOT / "data" / filename).exists():
            continue
        data = json.loads((ROOT / "data" / filename).read_text())
        collections.append({"name": name, "path": f"data/{filename}", "count": len(data["items"]),
                            "evidence": "local-recordings-and-dom-facts" if name == "captures" else "licensed-design-analysis" if name == "design-md" else "linked-metadata"})
    write("data/library-manifest.json", json.dumps({"version": 1, "collections": collections,
          "skill": ".agents/skills/frontend-library/SKILL.md", "query": "scripts/query-library.py",
          "viewer": "library/index.html", "sourcePolicies": "data/source-policies.json",
          "mcp": "scripts/library-mcp.py", "note": "Capture packages and design records may overlap link catalogs. Do not sum collections as unique websites."}, indent=2))
    print(f"Built {len(items)} evidence guides, {videos} video links and the agent manifest")


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Attach the official preview thumbnail to each transitions.dev entry.

    python3 scripts/enrich-transitions-previews.py

transitions.dev disallows AI crawlers (ClaudeBot, anthropic-ai, GPTBot) in robots.txt, so the site
itself is not fetched. Instead this reads the file tree of the author's public repository
(github.com/Jakubantalik/transitions.dev) at its current default-branch commit through `gh api`
and links each transition's thumbnail, `assets/community/thumbs/<slug>.jpg` (and `-dark.jpg`),
pinned to that commit on raw.githubusercontent.com.

No image or code is copied into this repository: the repo's licence permits using the transitions
but forbids redistributing the library, so previews are links only.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/transitions.json"
REPO = "Jakubantalik/transitions.dev"


def gh(path):
    out = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def main():
    sha = gh(f"repos/{REPO}/commits/main")["sha"]
    tree = {entry["path"] for entry in gh(f"repos/{REPO}/git/trees/{sha}?recursive=1")["tree"]}
    raw = f"https://raw.githubusercontent.com/{REPO}/{sha}/"
    catalog = json.loads(DATA.read_text())
    linked, missing = 0, []
    for item in catalog["items"]:
        for field in ("preview", "previewDark", "previewSource", "previewCommit", "previewNote"):
            item.pop(field, None)
        light = f"assets/community/thumbs/{item['slug']}.jpg"
        dark = f"assets/community/thumbs/{item['slug']}-dark.jpg"
        if light not in tree:
            missing.append(item["slug"])
            continue
        item["preview"] = raw + light
        if dark in tree:
            item["previewDark"] = raw + dark
        item.update({
            "previewSource": "repository-thumbnail",
            "previewCommit": sha,
            "previewNote": "Official thumbnail from github.com/Jakubantalik/transitions.dev at previewCommit, linked (not copied). transitions.dev itself was not crawled.",
        })
        linked += 1
    catalog["previews"] = {"repository": f"https://github.com/{REPO}", "commit": sha, "linked": linked, "missing": missing,
                           "note": "Thumbnails are linked from the author's repository; the library's licence forbids redistributing the transitions themselves."}
    DATA.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    print(f"linked {linked} thumbnails at {sha[:10]}; no thumbnail for: {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    main()

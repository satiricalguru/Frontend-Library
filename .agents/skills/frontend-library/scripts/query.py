#!/usr/bin/env python3
"""Search a local Frontend Library checkout. Python standard library only."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

COLLECTIONS = {
    "captures": "landing-pages.json",
    "styles": "refero-styles.json",
    "lusion": "lusion.json",
    "motion": "motion-examples.json",
    "transitions": "transitions.json",
    "godly": "godly.json",
    "fonts": "envato-award-fonts.json",
    "codrops": "codrops-webgl.json",
    "design-md": "design-md.json",
    "media-resources": "video-resources.json",
    "google-fonts": "google-fonts.json",
    "threejs": "threejs-examples.json",
    "icons": "open-icons.json",
}


def library_root(explicit=None):
    configured = explicit or os.environ.get("FRONTEND_LIBRARY_ROOT")
    candidates = [Path(configured).expanduser()] if configured else [
        Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents,
    ]
    for path in candidates:
        if (path / "data/refero-styles.json").is_file() and (path / "scripts/build-catalog.py").is_file():
            return path.resolve()
    raise ValueError("Library not found. Pass --library /path/to/Frontend-Library or set FRONTEND_LIBRARY_ROOT.")


def records(root, selected="all"):
    """Yield normalized records for CLI and read-only MCP retrieval."""
    for kind, filename in COLLECTIONS.items():
        if selected not in ("all", kind):
            continue
        path = root / "data" / filename
        if not path.exists():
            continue
        for item in json.loads(path.read_text())["items"]:
            identity = hashlib.sha256(item["url"].encode()).hexdigest()[:16]
            result = {"collection": kind, "catalog": str(path), **item}
            result.setdefault("id", f"{kind}-{identity}")
            for field in ("record", "video", "preview", "guide", "localDesignPath"):
                value = result.get(field)
                if isinstance(value, str) and value and not value.startswith(("http://", "https://")):
                    result[field] = str(root / value)
            yield result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="", help="All words must match; case insensitive")
    parser.add_argument("--library", help="Path to a Frontend Library checkout")
    parser.add_argument("--type", choices=["all", *COLLECTIONS], default="all")
    parser.add_argument("--tag", default="", help="Match a tag/category/description")
    parser.add_argument("--theme", choices=["light", "dark", "mixed"])
    parser.add_argument("--id", help="Exact captured page ID")
    parser.add_argument("--has-video", action="store_true")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable records")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    try:
        root = library_root(args.library)
        matches = []
        for item in records(root, args.type):
            searchable = json.dumps(item, ensure_ascii=False).lower()
            if not all(word in searchable for word in args.query.lower().split()):
                continue
            if args.tag.lower() not in searchable:
                continue
            if args.theme and item.get("theme") != args.theme:
                continue
            if args.id and item.get("id") != args.id:
                continue
            if args.has_video and not item.get("video"):
                continue
            matches.append(item)
        results = matches[:args.limit]
        if args.json:
            print(json.dumps({"library": str(root), "total": len(matches), "returned": len(results), "items": results}, ensure_ascii=False, indent=2))
        else:
            print(f"{len(matches)} matches; showing {len(results)}")
            for item in results:
                print(f"\n[{item['collection']}] {item['name']}\n  {item['url']}")
                for field in ("record", "video", "guide"):
                    if item.get(field):
                        print(f"  {field}: {item[field]}")
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

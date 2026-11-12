#!/usr/bin/env python3
"""Validate every catalog entry in data/.

Checks that each item carries the two fields the contributing guide requires
(the item's own ``url`` and the exact ``source`` page it was collected from),
that ``count`` matches the number of items, and that no entry is missing a
name. Run from the repo root:

    python3 scripts/validate-data.py

Exits non-zero and prints every problem it found, so it can be used as a CI
gate.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

FILES = [
    "refero-styles.json",
    "envato-award-fonts.json",
    "motion-examples.json",
    "godly.json",
    "transitions.json",
    "lusion.json",
    "landing-pages.json",
    "codrops-webgl.json",
    "design-md.json",
    "video-resources.json",
]

REQUIRED_FIELDS = ("name", "url", "source")


def validate(name):
    """Return a list of problem strings for one catalog file."""
    problems = []
    path = DATA / name
    if not path.exists():
        return [f"{name}: file is missing"]

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as err:
        return [f"{name}: invalid JSON ({err})"]

    items = data.get("items")
    if not isinstance(items, list):
        return [f"{name}: 'items' must be a list"]

    for index, item in enumerate(items):
        label = item.get("name") or f"#{index}"
        for field in REQUIRED_FIELDS:
            if not item.get(field):
                problems.append(f"{name}: '{label}' is missing '{field}'")

    count = data.get("count")
    if count is not None and count != len(items):
        problems.append(f"{name}: count is {count} but there are {len(items)} items")

    return problems


def main():
    problems = []
    for name in FILES:
        problems.extend(validate(name))

    if problems:
        print(f"{len(problems)} problem(s) found:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    total = sum(len(json.loads((DATA / n).read_text())["items"]) for n in FILES)
    print(f"ok: {total:,} catalog entries across {len(FILES)} files have a url and a source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

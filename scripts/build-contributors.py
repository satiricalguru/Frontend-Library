#!/usr/bin/env python3
"""Generate a single circular-avatar contributors SVG and update README.md.

    python3 scripts/build-contributors.py

Reads contributors from the GitHub REST API plus ``Co-authored-by:`` trailers
in git history so every human and AI/bot contributor appears in one combined
12-column circular avatar grid without waiting on external image caches.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = ROOT / ".github/assets/generated/contributors.svg"
README_PATH = ROOT / "README.md"
REPO = os.environ.get("GITHUB_REPOSITORY", "satiricalguru/Frontend-Library")

# The README shows the live grid served by api/contributors.js on the website, so new
# contributors appear without a commit. This script still writes OUT_SVG as an offline copy.
LIVE_URL = "https://frontendlibrary.vercel.app/api/contributors/"

START_MARKER = "<!-- CONTRIBUTORS:START -->"
END_MARKER = "<!-- CONTRIBUTORS:END -->"

TRAILER_ALIASES = [
    (re.compile(r"claude|anthropic", re.I), "claude"),
    (re.compile(r"copilot", re.I), "Copilot"),
    (re.compile(r"codex|openai", re.I), "codex"),
    (re.compile(r"cursor", re.I), "cursoragent"),
]

AVATAR_SIZE = 64
GAP = 8
COLUMNS = 12


def github_get_json(url: str):
    """Fetch JSON from an HTTPS GitHub API endpoint."""
    if not url.startswith("https://api.github.com/"):
        raise ValueError(f"Unsupported API URL: {url}")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Frontend-Library-Contributors-Builder",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        raise


def fetch_avatar_data_uri(avatar_url: str) -> str:
    """Download an avatar image over HTTPS and return a data URI."""
    if not avatar_url.startswith("https://"):
        raise ValueError(f"Unsupported avatar URL: {avatar_url}")
    sep = "&" if "?" in avatar_url else "?"
    sized_url = f"{avatar_url}{sep}s=128"
    req = urllib.request.Request(
        sized_url,
        headers={"User-Agent": "Frontend-Library-Contributors-Builder"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        ctype = resp.headers.get_content_type() or "image/png"
        if not ctype.startswith("image/"):
            ctype = "image/png"
        encoded = base64.b64encode(resp.read()).decode("ascii")
        return f"data:{ctype};base64,{encoded}"


def collect_coauthors() -> list[str]:
    """Scan git commit trailers for Co-authored-by contributors."""
    out = subprocess.check_output(
        ["git", "-C", str(ROOT), "log", "--format=%b"],
        text=True,
    )
    found: dict[str, None] = {}
    noreply_re = re.compile(r"^\s*Co-authored-by:\s*.+?<\d+\+([^@>]+)@users\.noreply\.github\.com>", re.I)
    generic_re = re.compile(r"^\s*Co-authored-by:\s*(.+)$", re.I)

    for line in out.splitlines():
        m = noreply_re.match(line)
        if m:
            found.setdefault(m.group(1).strip(), None)
            continue
        gm = generic_re.match(line)
        if not gm:
            continue
        trailer = gm.group(1)
        for pattern, login in TRAILER_ALIASES:
            if pattern.search(trailer):
                found.setdefault(login, None)
                break
    return list(found.keys())


def gather_contributors() -> list[dict]:
    """Collect all contributors (humans + AI/bots) sorted by commit count."""
    raw = github_get_json(f"https://api.github.com/repos/{REPO}/contributors?per_page=100") or []
    by_lower: dict[str, dict] = {}
    for item in raw:
        login = item["login"]
        by_lower[login.lower()] = {
            "login": login,
            "contributions": item.get("contributions", 1),
            "avatar_url": item["avatar_url"],
        }

    for login_hint in collect_coauthors():
        if login_hint.lower() in by_lower:
            continue
        user = github_get_json(f"https://api.github.com/users/{login_hint}")
        if not user or not user.get("avatar_url"):
            continue
        login = user["login"]
        by_lower[login.lower()] = {
            "login": login,
            "contributions": 1,
            "avatar_url": user["avatar_url"],
        }

    entries = list(by_lower.values())
    for entry in entries:
        entry["data_uri"] = fetch_avatar_data_uri(entry["avatar_url"])

    entries.sort(key=lambda x: (-x["contributions"], x["login"].lower()))
    return entries


def render_grid_svg(items: list[dict], title: str) -> str:
    """Render a 12-column circular avatar grid SVG."""
    cols = min(COLUMNS, max(1, len(items)))
    rows = max(1, (len(items) + COLUMNS - 1) // COLUMNS)
    width = cols * AVATAR_SIZE + (cols - 1) * GAP
    height = rows * AVATAR_SIZE + (rows - 1) * GAP
    radius = AVATAR_SIZE / 2 - 1

    defs = []
    nodes = []
    for idx, item in enumerate(items):
        col = idx % COLUMNS
        row = idx // COLUMNS
        x = col * (AVATAR_SIZE + GAP)
        y = row * (AVATAR_SIZE + GAP)
        cx = AVATAR_SIZE / 2
        cy = AVATAR_SIZE / 2
        clip_id = f"clip-{idx}"
        label = f"{item['login']} ({item['contributions']} commit{'s' if item['contributions'] != 1 else ''})"
        defs.append(f'<clipPath id="{clip_id}"><circle cx="{cx}" cy="{cy}" r="{radius}"/></clipPath>')
        nodes.append(
            f'<g transform="translate({x},{y})">'
            f"<title>{escape(label)}</title>"
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="#0d1117"/>'
            f'<image x="1" y="1" width="{AVATAR_SIZE - 2}" height="{AVATAR_SIZE - 2}" '
            f'xlink:href="{item["data_uri"]}" clip-path="url(#{clip_id})" preserveAspectRatio="xMidYMid slice"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#d0d7de" stroke-opacity="0.7" stroke-width="1.5"/>'
            f"</g>"
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title>"
        f"<defs>{''.join(defs)}</defs>"
        f"{''.join(nodes)}"
        f"</svg>\n"
    )


def update_readme() -> None:
    """Replace the Contributors marker block in README.md with the avatar grid only."""
    text = README_PATH.read_text(encoding="utf-8")
    if START_MARKER not in text or END_MARKER not in text:
        raise RuntimeError(f"README.md must contain {START_MARKER} and {END_MARKER}")

    block = (
        f"{START_MARKER}\n"
        f'<a href="https://github.com/{REPO}/graphs/contributors">\n'
        f'  <img src="{LIVE_URL}" alt="Frontend Library contributors (updates automatically)">\n'
        f"</a>\n"
        f"{END_MARKER}"
    )

    pattern = re.compile(
        re.escape(START_MARKER) + r"[\s\S]*?" + re.escape(END_MARKER),
        re.MULTILINE,
    )
    updated = pattern.sub(lambda _: block, text, count=1)
    README_PATH.write_text(updated, encoding="utf-8")


def main() -> None:
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    contributors = gather_contributors()
    OUT_SVG.write_text(
        render_grid_svg(contributors, f"Frontend Library contributors ({len(contributors)})"),
        encoding="utf-8",
    )
    update_readme()
    print(f"updated contributors: {len(contributors)} total")


if __name__ == "__main__":
    main()

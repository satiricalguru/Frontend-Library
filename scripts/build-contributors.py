#!/usr/bin/env python3
"""Generate circular-avatar contributor SVGs and update the Contributors block in README.md.

    python3 scripts/build-contributors.py

Reads contributors from the GitHub REST API (or ``gh`` CLI locally) plus
``Co-authored-by:`` trailers in git history so both human contributors and AI/bot
accounts appear cleanly without waiting on external image caches.
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
OUT_DIR = ROOT / ".github/assets/generated"
README_PATH = ROOT / "README.md"
REPO = os.environ.get("GITHUB_REPOSITORY", "satiricalguru/Frontend-Library")

START_MARKER = "<!-- CONTRIBUTORS:START -->"
END_MARKER = "<!-- CONTRIBUTORS:END -->"

AI_BOT_LOGINS = {
    "codex",
    "cursoragent",
    "copilot",
    "claude",
    "dependabot[bot]",
    "github-actions[bot]",
}

TRAILER_ALIASES = [
    (re.compile(r"claude|anthropic", re.I), "claude", "https://github.com/claude"),
    (re.compile(r"copilot", re.I), "Copilot", "https://github.com/apps/copilot-swe-agent"),
    (re.compile(r"codex|openai", re.I), "codex", "https://github.com/codex"),
    (re.compile(r"cursor", re.I), "cursoragent", "https://github.com/cursoragent"),
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


def is_ai_or_bot(login: str, account_type: str) -> bool:
    """Return True if the contributor is a bot or AI coding agent."""
    lower = login.lower()
    return account_type == "Bot" or lower.endswith("[bot]") or lower in AI_BOT_LOGINS


def profile_url_for(login: str, html_url: str | None) -> str:
    """Return a clean GitHub profile or app URL for a contributor."""
    if html_url and html_url.startswith("https://"):
        return html_url
    if login == "Copilot":
        return "https://github.com/features/copilot"
    if login.endswith("[bot]"):
        return f"https://github.com/apps/{login[:-5]}"
    return f"https://github.com/{login}"


def collect_coauthors() -> list[tuple[str, str | None]]:
    """Scan git commit trailers for Co-authored-by contributors."""
    out = subprocess.check_output(
        ["git", "-C", str(ROOT), "log", "--format=%b"],
        text=True,
    )
    found: dict[str, str | None] = {}
    noreply_re = re.compile(r"^\s*Co-authored-by:\s*.+?<\d+\+([^@>]+)@users\.noreply\.github\.com>", re.I)
    generic_re = re.compile(r"^\s*Co-authored-by:\s*(.+)$", re.I)

    for line in out.splitlines():
        m = noreply_re.match(line)
        if m:
            login = m.group(1).strip()
            found.setdefault(login.lower(), None)
            continue
        gm = generic_re.match(line)
        if not gm:
            continue
        trailer = gm.group(1)
        for pattern, login, url in TRAILER_ALIASES:
            if pattern.search(trailer):
                found.setdefault(login, url)
                break
    return list(found.items())


def gather_contributors() -> tuple[list[dict], list[dict]]:
    """Collect and split contributors into (humans, ai_and_bots)."""
    raw = github_get_json(f"https://api.github.com/repos/{REPO}/contributors?per_page=100") or []
    by_lower: dict[str, dict] = {}
    for item in raw:
        login = item["login"]
        by_lower[login.lower()] = {
            "login": login,
            "type": item.get("type", "User"),
            "contributions": item.get("contributions", 1),
            "avatar_url": item["avatar_url"],
            "html_url": profile_url_for(login, item.get("html_url")),
        }

    for login_hint, fallback_url in collect_coauthors():
        if login_hint.lower() in by_lower:
            continue
        user = github_get_json(f"https://api.github.com/users/{login_hint}")
        if not user or not user.get("avatar_url"):
            continue
        login = user["login"]
        by_lower[login.lower()] = {
            "login": login,
            "type": user.get("type", "User"),
            "contributions": 1,
            "avatar_url": user["avatar_url"],
            "html_url": profile_url_for(login, fallback_url or user.get("html_url")),
        }

    humans: list[dict] = []
    bots: list[dict] = []
    for entry in by_lower.values():
        entry["data_uri"] = fetch_avatar_data_uri(entry["avatar_url"])
        if is_ai_or_bot(entry["login"], entry["type"]):
            bots.append(entry)
        else:
            humans.append(entry)

    humans.sort(key=lambda x: (-x["contributions"], x["login"].lower()))
    bots.sort(key=lambda x: (-x["contributions"], x["login"].lower()))
    return humans, bots


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


def format_links(items: list[dict]) -> str:
    """Format compact inline profile links for a list of contributors."""
    return " · ".join(f'<a href="{escape(x["html_url"])}">@{escape(x["login"])}</a>' for x in items)


def update_readme(humans: list[dict], bots: list[dict]) -> None:
    """Replace the Contributors marker block in README.md."""
    text = README_PATH.read_text(encoding="utf-8")
    if START_MARKER not in text or END_MARKER not in text:
        raise RuntimeError(f"README.md must contain {START_MARKER} and {END_MARKER}")

    block = (
        f"{START_MARKER}\n"
        f"**Humans ({len(humans)})**\n\n"
        f'<a href="https://github.com/{REPO}/graphs/contributors">\n'
        f'  <img src=".github/assets/generated/contributors-humans.svg" alt="Human contributors to Frontend Library">\n'
        f"</a>\n\n"
        f"<sub>{format_links(humans)}</sub>\n\n"
        f"**AI & Bots ({len(bots)})**\n\n"
        f'<a href="https://github.com/{REPO}/graphs/contributors">\n'
        f'  <img src=".github/assets/generated/contributors-bots.svg" alt="AI and bot contributors to Frontend Library">\n'
        f"</a>\n\n"
        f"<sub>{format_links(bots)}</sub>\n"
        f"{END_MARKER}"
    )

    pattern = re.compile(
        re.escape(START_MARKER) + r"[\s\S]*?" + re.escape(END_MARKER),
        re.MULTILINE,
    )
    updated = pattern.sub(lambda _: block, text, count=1)
    README_PATH.write_text(updated, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    humans, bots = gather_contributors()
    (OUT_DIR / "contributors-humans.svg").write_text(
        render_grid_svg(humans, f"Human contributors ({len(humans)})"),
        encoding="utf-8",
    )
    (OUT_DIR / "contributors-bots.svg").write_text(
        render_grid_svg(bots, f"AI and bot contributors ({len(bots)})"),
        encoding="utf-8",
    )
    update_readme(humans, bots)
    print(f"updated contributors: {len(humans)} humans, {len(bots)} AI/bots")


if __name__ == "__main__":
    main()

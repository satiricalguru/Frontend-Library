#!/usr/bin/env python3
"""Generate the README's data-driven SVG visuals from data/*.json.

    python3 scripts/build-visuals.py

Writes to .github/assets/generated/. Everything is drawn from the catalog data,
so re-running after a data refresh keeps the README visuals in sync.
"""
import json
import re
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".github/assets/generated"
OUT.mkdir(parents=True, exist_ok=True)
FONT = "Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'SF Mono', Menlo, Consolas, monospace"
BG, PANEL, LINE, TEXT, MUTED = "#0b1020", "#121a30", "#24304f", "#e8eeff", "#8a97b8"
BLUE, SKY = "#2563eb", "#38bdf8"


def load(n):
    return json.loads((ROOT / "data" / n).read_text())


def lum(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title>'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{SKY}"/></linearGradient>'
            f'<radialGradient id="glow" cx="50%" cy="0%" r="80%"><stop offset="0" stop-color="#1d2b63"/><stop offset="1" stop-color="{BG}"/></radialGradient></defs>'
            f'<clipPath id="r"><rect width="{w}" height="{h}" rx="18"/></clipPath>'
            f'<g clip-path="url(#r)"><rect width="{w}" height="{h}" fill="url(#glow)"/>{body}</g></svg>\n')


counts = {
    "Design systems": (load("refero-styles.json")["count"], "Refero Styles", "#a78bfa"),
    "Award fonts": (load("envato-award-fonts.json")["count"], "Envato Elements", "#f472b6"),
    "Motion examples": (load("motion-examples.json")["count"], "motion.dev", SKY),
    "Godly picks": (load("godly.json")["count"], "godly.design", "#facc15"),
    "UI transitions": (load("transitions.json")["count"], "transitions.dev", "#34d399"),
    "3D projects & labs": (load("lusion.json")["count"], "lusion.co", "#fb923c"),
}
for filename, label, source, color in [
    ("design-md.json", "Design analyses", "VoltAgent", "#22d3ee"),
    ("codrops-webgl.json", "WebGL references", "Codrops", "#c084fc"),
    ("video-resources.json", "Landing media & tools", "Brad Traversy", "#bef264"),
]:
    if (ROOT / "data" / filename).exists():
        counts[label] = (load(filename)["count"], source, color)
TOTAL = sum(v[0] for v in counts.values())


# ---------------------------------------------------------------- hero banner
def hero():
    styles = [s for s in load("refero-styles.json")["items"] if len(s["colors"]) >= 2]
    stripes, x = "", 0
    for s in styles[:: max(1, len(styles) // 64)][:64]:
        for c in s["colors"][:2]:
            stripes += f'<rect x="{x}" y="0" width="10" height="8" fill="{c["hex"]}"/>'
            x += 10
    w, h = 1280, 420
    body = f'<g transform="translate(0,{h - 8})">{stripes}</g>'
    body += f'<text x="64" y="120" fill="{MUTED}" font-family="{MONO}" font-size="16" letter-spacing="3">OPEN-SOURCE · CURATED · SOURCE-TRACKED</text>'
    body += f'<text x="62" y="196" fill="{TEXT}" font-family="{FONT}" font-size="74" font-weight="800" letter-spacing="-2">Frontend Library</text>'
    body += f'<text x="64" y="246" fill="{MUTED}" font-family="{FONT}" font-size="23">Landing-page references, design data &amp; motion — <tspan fill="url(#g)" font-weight="700">{TOTAL:,} indexed entries</tspan>, all source-linked.</text>'
    x = 64
    featured = ["Design systems", "Design analyses", "WebGL references", "Motion examples", "Landing media & tools", "3D projects & labs"]
    for label in [name for name in featured if name in counts]:
        n, src, col = counts[label]
        body += f'<g transform="translate({x},292)"><rect width="182" height="86" rx="14" fill="{PANEL}" stroke="{LINE}"/>'
        body += f'<circle cx="20" cy="24" r="5" fill="{col}"/><text x="32" y="29" fill="{MUTED}" font-family="{FONT}" font-size="13">{escape(src)}</text>'
        body += f'<text x="16" y="62" fill="{TEXT}" font-family="{FONT}" font-size="28" font-weight="800">{n:,}</text>'
        body += f'<text x="16" y="78" fill="{MUTED}" font-family="{FONT}" font-size="11">{escape(label)}</text></g>'
        x += 194
    (OUT / "hero.svg").write_text(svg(w, h, body, f"Frontend Library — {TOTAL:,} curated frontend entries"))


# ---------------------------------------------------------------- source bars
def source_bars():
    w, row = 880, 46
    h = 90 + row * len(counts)
    mx = max(v[0] for v in counts.values())
    body = f'<text x="32" y="48" fill="{TEXT}" font-family="{FONT}" font-size="22" font-weight="800">What&#8217;s inside</text>'
    body += f'<text x="{w - 32}" y="48" text-anchor="end" fill="{MUTED}" font-family="{FONT}" font-size="14">{TOTAL:,} entries · 6 sources</text>'
    for i, (label, (n, src, col)) in enumerate(sorted(counts.items(), key=lambda kv: -kv[1][0])):
        y = 78 + i * row
        bw = max(6, (w - 330) * n / mx)
        body += f'<text x="32" y="{y + 20}" fill="{TEXT}" font-family="{FONT}" font-size="15" font-weight="600">{escape(label)}</text>'
        body += f'<text x="32" y="{y + 36}" fill="{MUTED}" font-family="{FONT}" font-size="11">{escape(src)}</text>'
        body += f'<rect x="210" y="{y + 8}" width="{w - 330}" height="22" rx="11" fill="{PANEL}"/>'
        body += f'<rect x="210" y="{y + 8}" width="{bw:.0f}" height="22" rx="11" fill="{col}"/>'
        body += f'<text x="{w - 32}" y="{y + 25}" text-anchor="end" fill="{TEXT}" font-family="{MONO}" font-size="15" font-weight="700">{n:,}</text>'
    (OUT / "sources-chart.svg").write_text(svg(w, h, body, "Entries per source"))


# ---------------------------------------------------------------- palette wall
def palette_wall():
    want = ["Linear", "Vercel", "Stripe", "Notion", "Raycast", "Figma", "Spotify", "Airbnb", "OpenAI", "Framer", "Supabase", "Arc",
            "Wise", "Superhuman", "GitHub", "Discord", "Duolingo", "Slack", "Shopify", "Intercom", "Mailchimp", "Revolut", "Tesla",
            "Netflix", "Coinbase", "Anthropic", "Mercury", "Ramp", "Cursor", "Lovable", "Resend", "Clerk", "Retool", "Canva", "Lego", "Monzo"]
    by = {s["name"]: s for s in load("refero-styles.json")["items"]}
    tiles = []
    for n in want:
        s = by.get(n)
        if not s or len(s["colors"]) < 2:
            continue
        cs = [c["hex"] for c in s["colors"]]
        pairs = sorted(((contrast(a, b), a, b) for a in cs for b in cs if a != b), reverse=True)
        score, bg, fg = pairs[0]
        if score < 4.5:  # palette too tonal to read: keep brand bg, pick legible ink
            bg = max(cs, key=lambda c: abs(lum(c) - 0.18))
            fg = "#ffffff" if contrast(bg, "#ffffff") >= contrast(bg, "#0b1020") else "#0b1020"
        tiles.append((n, s, bg, fg))
    cols, tw, th, gap = 6, 182, 112, 12
    rows = (len(tiles) + cols - 1) // cols
    w, h = 32 * 2 + cols * tw + (cols - 1) * gap, 92 + rows * (th + gap) + 24
    body = f'<text x="32" y="48" fill="{TEXT}" font-family="{FONT}" font-size="22" font-weight="800">Brand palettes from the Refero index</text>'
    body += f'<text x="{w - 32}" y="48" text-anchor="end" fill="{MUTED}" font-family="{FONT}" font-size="14">each tile is set in the brand&#8217;s own palette</text>'
    for i, (n, s, bg, fg) in enumerate(tiles):
        x, y = 32 + (i % cols) * (tw + gap), 72 + (i // cols) * (th + gap)
        body += f'<g transform="translate({x},{y})"><rect width="{tw}" height="{th}" rx="14" fill="{bg}" stroke="{LINE}"/>'
        body += f'<text x="14" y="42" fill="{fg}" font-family="{FONT}" font-size="22" font-weight="800" letter-spacing="-.5">{escape(n)}</text>'
        body += f'<text x="14" y="{th - 16}" fill="{fg}" fill-opacity=".75" font-family="{MONO}" font-size="11">{" · ".join(c["hex"] for c in s["colors"][:2])}</text>'
        for j, c in enumerate(s["colors"][:4]):
            body += f'<circle cx="{tw - 18 - j * 16}" cy="20" r="6" fill="{c["hex"]}" stroke="{fg}" stroke-opacity=".35"/>'
        body += "</g>"
    (OUT / "palette-wall.svg").write_text(svg(w, h, body, "Brand palettes from the Refero index"))


# ---------------------------------------------------------------- theme + category chart
def refero_breakdown():
    items = load("refero-styles.json")["items"]
    cats = Counter(s["category"] for s in items).most_common()
    th = Counter(s["theme"] for s in items)
    w, h = 880, 360
    body = f'<text x="32" y="48" fill="{TEXT}" font-family="{FONT}" font-size="22" font-weight="800">{len(items):,} design systems by industry</text>'
    mx = cats[0][1]
    bw = (w - 64 - (len(cats) - 1) * 10) / len(cats)
    for i, (c, n) in enumerate(cats):
        x = 32 + i * (bw + 10)
        bh = 200 * n / mx
        body += f'<rect x="{x:.1f}" y="{280 - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="8" fill="url(#g)" fill-opacity="{0.45 + 0.55 * n / mx:.2f}"/>'
        body += f'<text x="{x + bw / 2:.1f}" y="{272 - bh:.1f}" text-anchor="middle" fill="{TEXT}" font-family="{MONO}" font-size="12" font-weight="700">{n}</text>'
        body += f'<text x="{x + bw / 2:.1f}" y="300" text-anchor="middle" fill="{MUTED}" font-family="{FONT}" font-size="11">{escape(c)}</text>'
    tot = sum(th.values())
    x = 32
    for key, col, lab in (("light", "#f8fafc", "light"), ("dark", "#1e293b", "dark"), ("mixed", "#64748b", "mixed")):
        ww = (w - 64) * th[key] / tot
        body += f'<rect x="{x:.1f}" y="318" width="{ww:.1f}" height="18" fill="{col}" stroke="{LINE}"/>'
        body += f'<text x="{x + 8:.1f}" y="331" fill="{"#0b1020" if key == "light" else TEXT}" font-family="{FONT}" font-size="11" font-weight="600">{lab} {th[key]}</text>'
        x += ww
    (OUT / "refero-breakdown.svg").write_text(svg(w, h, body, "Refero design systems by industry and theme"))


# ---------------------------------------------------------------- motion categories
def motion_chart():
    items = load("motion-examples.json")["items"]
    cats = Counter(c for x in items for c in x["categories"][:1]).most_common(12)
    w, row = 880, 30
    h = 80 + row * len(cats)
    mx = cats[0][1]
    body = f'<text x="32" y="48" fill="{TEXT}" font-family="{FONT}" font-size="22" font-weight="800">Top Motion example categories</text>'
    for i, (c, n) in enumerate(cats):
        y = 66 + i * row
        body += f'<text x="32" y="{y + 16}" fill="{TEXT}" font-family="{FONT}" font-size="14">{escape(c.replace("-", " ").title())}</text>'
        body += f'<rect x="230" y="{y + 4}" width="{(w - 330) * n / mx:.0f}" height="16" rx="8" fill="{SKY}" fill-opacity="{0.4 + 0.6 * n / mx:.2f}"/>'
        body += f'<text x="{w - 32}" y="{y + 17}" text-anchor="end" fill="{MUTED}" font-family="{MONO}" font-size="13">{n}</text>'
    (OUT / "motion-chart.svg").write_text(svg(w, h, body, "Top Motion example categories"))


# ---------------------------------------------------------------- font specimen
def font_specimen():
    fonts = load("envato-award-fonts.json")["items"]
    pick = {}
    for f in fonts:
        pick.setdefault(f["category"], []).append(f["name"])
    styles = {"script-and-handwritten": ("'Snell Roundhand', 'Brush Script MT', cursive", "italic", 400),
              "serif": ("Didot, 'Bodoni 72', Georgia, serif", "normal", 700),
              "decorative": ("'Rockwell', 'Copperplate', Impact, fantasy", "normal", 700),
              "sans-serif": (FONT, "normal", 800)}
    w, h = 720, 450
    body = f'<text x="32" y="48" fill="{MUTED}" font-family="{MONO}" font-size="13" letter-spacing="2">ENVATO · FONTS / AWARDS · {len(fonts):,} TYPEFACES</text>'
    y = 110
    for cat, (fam, st, wt) in styles.items():
        names = [n for n in pick.get(cat, []) if len(n) < 28][:3]
        if not names:
            continue
        clean = re.sub(r"\s*[-–]\s*.*$", "", names[0])
        body += f'<text x="32" y="{y}" fill="{TEXT}" font-family="{fam}" font-style="{st}" font-weight="{wt}" font-size="46">{escape(clean)}</text>'
        body += f'<text x="34" y="{y + 24}" fill="{MUTED}" font-family="{FONT}" font-size="12">{escape(cat.replace("-", " "))} · also {escape(", ".join(re.sub(r"[-–].*$", "", n).strip() for n in names[1:]))}</text>'
        y += 86
    body += f'<text x="{w - 32}" y="{h - 22}" text-anchor="end" fill="{MUTED}" font-family="{FONT}" font-size="11">names set in system fonts · premium files stay on Envato</text>'
    (OUT / "font-specimen.svg").write_text(svg(w, h, body, "Envato award fonts specimen"))


if __name__ == "__main__":
    for f in (hero, source_bars, palette_wall, refero_breakdown, motion_chart, font_specimen):
        f()
    print("wrote", sorted(p.name for p in OUT.iterdir()))

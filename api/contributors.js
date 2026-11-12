/* Live contributors avatar grid for the README.
 *
 *   GET /api/contributors/  ->  image/svg+xml   (trailing slash: vercel.json sets trailingSlash)
 *
 * Same output as scripts/build-contributors.py (12-column circular avatars, humans + AI/bot
 * co-authors from `Co-authored-by:` trailers), but generated on request and cached at the edge
 * for an hour. The README links here, so new contributors and changed GitHub photos appear
 * without a commit, a PR or a workflow.
 * Avatars are embedded as data URIs because an SVG shown as an <img> cannot load external images.
 */
'use strict';

const REPO = 'satiricalguru/Frontend-Library';
const SIZE = 64;
const GAP = 8;
const COLUMNS = 12;
const ALIASES = [
  [/claude|anthropic/i, 'claude'],
  [/copilot/i, 'Copilot'],
  [/codex|openai/i, 'codex'],
  [/cursor/i, 'cursoragent'],
  [/devin/i, 'devin-ai-integration[bot]'],
  [/opencode/i, 'opencode-agent[bot]'],
];

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[c]));

async function gh(path) {
  const headers = { Accept: 'application/vnd.github+json', 'User-Agent': 'Frontend-Library-Contributors' };
  if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  const r = await fetch(`https://api.github.com${path}`, { headers });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`GitHub ${r.status} for ${path}`);
  return r.json();
}

async function dataUri(url) {
  const r = await fetch(`${url}${url.includes('?') ? '&' : '?'}s=96`);
  if (!r.ok) throw new Error(`avatar ${r.status}`);
  const type = (r.headers.get('content-type') || 'image/png').split(';')[0];
  return `data:${type.startsWith('image/') ? type : 'image/png'};base64,${Buffer.from(await r.arrayBuffer()).toString('base64')}`;
}

async function gather() {
  const people = new Map();
  for (const c of (await gh(`/repos/${REPO}/contributors?per_page=100`)) || []) {
    people.set(c.login.toLowerCase(), { login: c.login, contributions: c.contributions || 1, avatar: c.avatar_url });
  }
  // co-authors from commit trailers (first 300 commits)
  const hints = new Map();
  for (let page = 1; page <= 3; page++) {
    const commits = (await gh(`/repos/${REPO}/commits?per_page=100&page=${page}`)) || [];
    for (const c of commits) {
      for (const line of (c.commit?.message || '').split('\n')) {
        const m = line.match(/^\s*Co-authored-by:\s*(.+)$/i);
        if (!m) continue;
        const noreply = m[1].match(/<\d+\+([^@>]+)@users\.noreply\.github\.com>/i);
        const login = noreply ? noreply[1] : (ALIASES.find(([re]) => re.test(m[1])) || [])[1];
        if (login) hints.set(login.toLowerCase(), { login, n: (hints.get(login.toLowerCase())?.n || 0) + 1 });
      }
    }
    if (commits.length < 100) break;
  }
  for (const [key, { login, n }] of hints) {
    if (people.has(key)) continue;
    const user = await gh(`/users/${encodeURIComponent(login)}`);
    if (user?.avatar_url) people.set(user.login.toLowerCase(), { login: user.login, contributions: n, avatar: user.avatar_url });
  }
  const list = [...people.values()].sort((a, b) => b.contributions - a.contributions || a.login.localeCompare(b.login));
  await Promise.all(list.map(async (p) => { try { p.uri = await dataUri(p.avatar); } catch { p.uri = null; } }));
  return list;
}

function render(items) {
  const cols = Math.min(COLUMNS, Math.max(1, items.length));
  const rows = Math.max(1, Math.ceil(items.length / COLUMNS));
  const w = cols * SIZE + (cols - 1) * GAP;
  const h = rows * SIZE + (rows - 1) * GAP;
  const r = SIZE / 2 - 1;
  const defs = [], nodes = [];
  items.forEach((p, i) => {
    const x = (i % COLUMNS) * (SIZE + GAP), y = Math.floor(i / COLUMNS) * (SIZE + GAP);
    const label = `${p.login} (${p.contributions} commit${p.contributions === 1 ? '' : 's'})`;
    defs.push(`<clipPath id="c${i}"><circle cx="${SIZE / 2}" cy="${SIZE / 2}" r="${r}"/></clipPath>`);
    nodes.push(`<g transform="translate(${x},${y})"><title>${esc(label)}</title>` +
      `<circle cx="${SIZE / 2}" cy="${SIZE / 2}" r="${r}" fill="#0d1117"/>` +
      (p.uri ? `<image x="1" y="1" width="${SIZE - 2}" height="${SIZE - 2}" href="${p.uri}" xlink:href="${p.uri}" clip-path="url(#c${i})" preserveAspectRatio="xMidYMid slice"/>`
        : `<text x="${SIZE / 2}" y="${SIZE / 2 + 7}" text-anchor="middle" font-family="Arial,sans-serif" font-size="20" fill="#d0d7de">${esc(p.login.slice(0, 2).toUpperCase())}</text>`) +
      `<circle cx="${SIZE / 2}" cy="${SIZE / 2}" r="${r}" fill="none" stroke="#d0d7de" stroke-opacity="0.7" stroke-width="1.5"/></g>`);
  });
  const title = `Frontend Library contributors (${items.length})`;
  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title><defs>${defs.join('')}</defs>${nodes.join('')}</svg>`;
}

module.exports = async (req, res) => {
  try {
    const svg = render(await gather());
    res.setHeader('Content-Type', 'image/svg+xml; charset=utf-8');
    // Cache briefly (1 min) so newly merged contributors appear without long delay
    res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=60, stale-while-revalidate=300');
    res.status(200).send(svg);
  } catch (err) {
    res.setHeader('Content-Type', 'image/svg+xml; charset=utf-8');
    res.setHeader('Cache-Control', 'public, max-age=300, s-maxage=300');
    res.status(200).send(`<svg xmlns="http://www.w3.org/2000/svg" width="420" height="40" role="img" aria-label="Contributors temporarily unavailable"><text x="0" y="26" font-family="Arial,sans-serif" font-size="14" fill="#8b949e">Contributors temporarily unavailable — see the contributors graph.</text></svg>`);
  }
};

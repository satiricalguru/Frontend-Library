/* Frontend Library — library viewer.
 * All catalog text is external, untrusted metadata: it is rendered with DOM APIs (textContent),
 * never parsed as HTML, and every link goes through safeUrl().
 */
'use strict';

const COLLECTIONS = {
  captures:          { file: 'landing-pages.json',       label: 'Captured pages',   short: 'Capture',    dot: '#3ee08f' },
  styles:            { file: 'refero-styles.json',       label: 'Design systems',   short: 'Refero style', dot: '#a78bfa' },
  'design-md':       { file: 'design-md.json',           label: 'DESIGN.md',        short: 'DESIGN.md',  dot: '#f59e0b' },
  codrops:           { file: 'codrops-webgl.json',       label: 'WebGL & demos',    short: 'Codrops',    dot: '#f472b6' },
  motion:            { file: 'motion-examples.json',     label: 'Motion',           short: 'Motion',     dot: '#38bdf8' },
  transitions:       { file: 'transitions.json',         label: 'Transitions',      short: 'Transition', dot: '#34d399' },
  godly:             { file: 'godly.json',               label: 'Godly',            short: 'Godly',      dot: '#facc15' },
  lusion:            { file: 'lusion.json',              label: 'Lusion index',     short: 'Lusion',     dot: '#fb923c' },
  fonts:             { file: 'envato-award-fonts.json',  label: 'Fonts',            short: 'Font',       dot: '#e879f9' },
  'media-resources': { file: 'video-resources.json',     label: 'Resources',        short: 'Resource',   dot: '#94a3b8' },
  'google-fonts':    { file: 'google-fonts.json',        label: 'Google Fonts',     short: 'Google Font', dot: '#60a5fa' },
  threejs:           { file: 'threejs-examples.json',    label: 'Three.js',         short: 'Three.js',   dot: '#22d3ee' },
  icons:             { file: 'open-icons.json',          label: 'Icons',            short: 'Icon',       dot: '#c084fc' },
  showcases:         { file: 'showcases.json',           label: 'Showcases',        short: 'Showcase',   dot: '#f43f5e' },
};
const loadedFonts = new Set();
function loadGoogleFont(family) {
  // only the glyphs of the family name are requested (text=), so each card costs a few KB
  if (loadedFonts.has(family) || loadedFonts.size > 400) return;
  loadedFonts.add(family);
  const l = document.createElement('link');
  l.rel = 'stylesheet';
  l.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(family).replace(/%20/g, '+')}&text=${encodeURIComponent(family + 'Aa')}&display=swap`;
  document.head.append(l);
}
const PAGE = 36;
const BASE = new URL('../', location.href);
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const canHover = matchMedia('(hover: hover)').matches;

const $ = (s) => document.querySelector(s);
const grid = $('#results'), status = $('#status'), search = $('#search'), more = $('#more');
const chipsEl = $('#collections'), themesEl = $('#themes'), drawer = $('#drawer');

const state = { q: '', type: 'all', theme: '', view: 'grid', shown: PAGE };
const loaded = {};           // collection -> records
const counts = {};           // collection -> count from manifest
let matching = [];

/* ── helpers ─────────────────────────────────────────── */
function node(tag, className, text) {
  const n = document.createElement(tag);
  if (className) n.className = className;
  if (text !== undefined && text !== null) n.textContent = text;
  return n;
}
function safeUrl(value) {
  if (typeof value !== 'string' || !value || value.startsWith('//')) return null;
  try { const u = new URL(value, BASE); return ['http:', 'https:'].includes(u.protocol) ? u.href : null; } catch { return null; }
}
const REPO_BLOB = 'https://github.com/satiricalguru/Frontend-Library/blob/main/';
function link(text, value, cls = 'pill') {
  const a = node('a', cls, text);
  // repo Markdown renders on GitHub; served raw by the static host it would show as plain text
  if (typeof value === 'string' && /^(?![a-z]+:|\/\/)[\w./-]+\.md$/i.test(value)) value = REPO_BLOB + value.replace(/^\.?\//, '');
  const href = safeUrl(value);
  a.href = href || '#';
  if (href && new URL(href).origin !== location.origin) { a.target = '_blank'; a.rel = 'noopener noreferrer'; }
  return a;
}
function domain(value) { try { return new URL(value, BASE).hostname.replace(/^www\./, ''); } catch { return ''; } }
function hash(str) { let h = 0; for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) | 0; return Math.abs(h); }
const HEX = /^#[0-9a-f]{3}([0-9a-f]{3})?$/i;
function lum(hex) {
  let h = hex.slice(1); if (h.length === 3) h = [...h].map((c) => c + c).join('');
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
const contrast = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05); };
function pair(colors) {
  const cs = (colors || []).map((c) => c.hex).filter((h) => HEX.test(h));
  if (!cs.length) return ['#f1f2f6', '#0a0b10', cs];
  let best = [0, cs[0], cs[1] || '#0a0b10'];
  for (const a of cs) for (const b of cs) if (a !== b) { const c = contrast(a, b); if (c > best[0]) best = [c, a, b]; }
  let [score, bg, fg] = best;
  if (score < 4.5) fg = contrast(bg, '#ffffff') > contrast(bg, '#0a0b10') ? '#ffffff' : '#0a0b10';
  return [bg, fg, cs];
}
let toastTimer = 0;
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('is-on'); clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove('is-on'), 1800); }
async function copy(text) { try { await navigator.clipboard.writeText(text); toast(`Copied ${text}`); } catch { toast(text); } }

/* ── visuals per collection ──────────────────────────── */
const isDark = () => document.documentElement.dataset.theme ? document.documentElement.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
function visual(item, { large = false } = {}) {
  const v = node('div', 'card-visual');
  const c = item.collection;
  if ((c === 'captures' || c === 'lusion') && safeUrl(item.preview)) {
    const img = node('img'); img.src = safeUrl(item.preview); img.alt = `Captured viewport of ${item.name}`;
    img.loading = 'lazy'; img.decoding = 'async';
    if (item.viewport?.mobile) img.className = 'mobile';
    img.addEventListener('error', () => imageFailed(img, v, item), { once: true });
    v.append(img);
    const label = c === 'lusion' ? (item.type === 'labs' ? 'Labs experiment' : 'Case study') : item.viewport ? `${item.viewport.width}×${item.viewport.height}` : item.status;
    const b = node('span', `badge${(item.status || item.captureStatus) === 'captured' ? ' live' : ''}`, label);
    v.append(b);
    if (large && safeUrl(item.video)) {
      const vid = node('video'); vid.src = safeUrl(item.video); vid.muted = true; vid.loop = true; vid.playsInline = true; vid.controls = true; vid.preload = 'metadata'; vid.poster = safeUrl(item.preview); vid.autoplay = !reduced;
      vid.setAttribute('aria-label', `Scroll recording of ${item.name}`);
      v.append(vid); v.classList.add('is-playing');
    }
    return v;
  }
  if (c === 'styles') {
    const [bg, fg, cs] = pair(item.colors);
    v.classList.add('v-brand'); v.style.background = bg; v.style.color = fg; v.style.borderColor = 'transparent';
    const bar = node('div', 'bar'); cs.slice(0, 6).forEach((h) => { const i = node('i'); i.style.background = h; bar.append(i); });
    v.append(node('small', '', [item.theme, item.category].filter(Boolean).join(' · ')), node('b', '', item.name), bar);
    return v;
  }
  if (c === 'showcases' && safeUrl(item.preview)) {
    const img = node('img'); img.src = safeUrl(item.preview); img.alt = `Still from ${item.name}`;
    img.loading = 'lazy'; img.decoding = 'async'; img.referrerPolicy = 'no-referrer';
    img.addEventListener('error', () => imageFailed(img, v, item), { once: true });
    v.append(img, node('span', 'badge live', item.category || 'showcase'));
    return v;
  }
  if (c === 'transitions' && safeUrl(item.preview)) {
    const img = node('img');
    img.src = safeUrl(isDark() && item.previewDark ? item.previewDark : item.preview);
    img.alt = `Preview of the ${item.name} transition`; img.loading = 'lazy'; img.decoding = 'async'; img.referrerPolicy = 'no-referrer';
    img.addEventListener('error', () => imageFailed(img, v, item), { once: true });
    v.append(img, node('span', 'badge', 'transition'));
    return v;
  }
  if (c === 'codrops' && safeUrl(item.preview)) {
    const img = node('img'); img.src = safeUrl(item.preview); img.alt = `Preview of ${item.name}`;
    // GitHub's generated repo card is a wide text layout: show it whole instead of cropping it
    if (item.previewSource === 'github-social-card') img.className = 'contain';
    img.loading = 'lazy'; img.decoding = 'async'; img.referrerPolicy = 'no-referrer';
    img.addEventListener('error', () => imageFailed(img, v, item), { once: true });
    v.append(img, node('span', 'badge', item.kind === 'article-reference' ? 'article' : 'demo repo'));
    return v;
  }
  if (c === 'threejs' && safeUrl(item.preview)) {
    const img = node('img'); img.src = safeUrl(item.preview); img.alt = `Screenshot of the three.js example ${item.name}`;
    img.loading = 'lazy'; img.decoding = 'async';
    img.addEventListener('error', () => imageFailed(img, v, item), { once: true });
    v.append(img, node('span', 'badge', item.category));
    return v;
  }
  if (c === 'icons' && safeUrl(item.svg)) {
    v.classList.add('v-icon');
    const img = node('img'); img.src = safeUrl(item.svg); img.alt = `${item.name} icon`; img.loading = 'lazy'; img.decoding = 'async';
    img.width = 64; img.height = 64;
    v.append(img, node('span', 'k', item.set));
    return v;
  }
  if (c === 'google-fonts') {
    loadGoogleFont(item.name);
    v.classList.add('v-font', 'gf');
    const b = node('b', '', item.name); b.style.fontFamily = `'${item.name.replace(/'/g, '')}', var(--display)`;
    v.append(b, node('span', 'k', [item.category, item.axes?.length ? 'variable' : `${item.styles} styles`].filter(Boolean).join(' · ')));
    return v;
  }
  if (c === 'fonts') {
    const cat = item.category || '';
    const cls = cat.includes('script') ? 'script' : cat === 'serif' ? 'serif' : cat === 'decorative' ? 'decorative' : 'sans';
    v.classList.add('v-font', cls);
    v.append(node('b', '', item.name.replace(/\s*[-–—|].*$/, '')));
    return v;
  }
  return typeVisual(item, v);
}
// a preview that fails to load (404, rate limit) turns its own frame into the typographic tile
function imageFailed(img, v, item) {
  img.remove();
  v.querySelectorAll('.badge, video').forEach((n) => n.remove());
  v.classList.remove('is-playing');
  typeVisual(item, v);
}
function typeVisual(item, v = node('div', 'card-visual')) {
  const h = hash(item.name + item.collection);
  v.classList.add('v-type');
  if (item.collection === 'design-md' || item.collection === 'media-resources') v.classList.add('light');
  v.style.setProperty('--h', String(200 + (h % 140)));
  v.style.setProperty('--gx', `${30 + (h % 50)}%`);
  v.style.setProperty('--gy', `${20 + ((h >> 3) % 50)}%`);
  const kind = item.platform || item.kind?.replace(/-/g, ' ') || item.section || COLLECTIONS[item.collection].short;
  v.append(node('span', 'k', kind), node('b', '', item.name), node('span', 'dom', domain(item.url)));
  return v;
}

function subtitle(item) {
  const bits = [];
  if (item.collection === 'styles') bits.push((item.fonts || []).slice(0, 2).join(', '));
  else if (item.collection === 'lusion') bits.push([(item.tags || []).slice(0, 3).join(' · '), item.video ? 'hover to play' : ''].filter(Boolean).join(' · '));
  else if (item.collection === 'captures') bits.push([item.group === 'refero' ? 'brand homepage · via Refero' : 'Lusion', ...(item.tags || []).filter((t) => t !== 'lusion' && t !== 'refero' && t !== 'landing-page').slice(0, 2)].join(' · '));
  else if (item.description) bits.push(item.description);
  else bits.push([item.category, ...(item.tags || [])].filter(Boolean).slice(0, 3).join(' · '));
  return bits.join(' ').trim() || domain(item.url);
}

/* ── cards ───────────────────────────────────────────── */
const cardCache = new Map();
const keyOf = (it) => `${it.collection}|${it.id || it.url}|${it.name}`;
function cardFor(item, i) {
  const k = keyOf(item);
  if (!cardCache.has(k)) {
    const el = card(item, i);
    el.addEventListener('animationend', () => el.classList.add('is-shown'), { once: true });
    cardCache.set(k, el);
  }
  return cardCache.get(k);
}
function card(item, i) {
  const a = node('article', 'card');
  a.style.setProperty('--i', String(i % PAGE));
  const v = visual(item);
  const hit = node('button', 'card-hit'); hit.type = 'button';
  hit.setAttribute('aria-label', `${item.name} — ${COLLECTIONS[item.collection].short}. Open details`);
  hit.addEventListener('click', () => openDrawer(item));
  const meta = node('div', 'card-meta');
  meta.append(node('h2', '', item.name), node('span', '', COLLECTIONS[item.collection].short));
  a.append(v, meta, node('p', 'card-sub', subtitle(item)), hit);
  if ((item.collection === 'captures' || item.collection === 'lusion') && canHover && !reduced && safeUrl(item.video)) {
    let vid = null;
    a.addEventListener('pointerenter', () => {
      vid = node('video'); vid.src = safeUrl(item.video); vid.muted = true; vid.loop = true; vid.playsInline = true; vid.preload = 'auto';
      vid.setAttribute('aria-hidden', 'true');
      v.append(vid);
      vid.play().then(() => v.classList.add('is-playing')).catch(() => {});
    });
    a.addEventListener('pointerleave', () => { v.classList.remove('is-playing'); if (vid) { vid.pause(); vid.remove(); vid = null; } });
  }
  return a;
}
function skeletons(n = 9) {
  return Array.from({ length: n }, () => { const s = node('div', 'card skeleton'); const m = node('div', 'card-meta'); m.append(node('i')); s.append(node('div', 'card-visual'), m); return s; });
}

/* ── drawer ──────────────────────────────────────────── */
function row(dl, label, value) {
  if (value === undefined || value === null || value === '' || (Array.isArray(value) && !value.length)) return;
  dl.append(node('dt', '', label));
  const dd = node('dd');
  if (value instanceof Node) dd.append(value); else dd.textContent = Array.isArray(value) ? value.join(', ') : String(value);
  dl.append(dd);
}
function openDrawer(item) {
  $('#drawer-kind').textContent = `${COLLECTIONS[item.collection].label}${item.kind ? ' · ' + item.kind.replace(/-/g, ' ') : ''}`;
  $('#drawer-title').textContent = item.name;
  $('#drawer-desc').textContent = item.description || '';
  $('#drawer-visual').replaceChildren(visual(item, { large: true }));
  const dl = $('#drawer-meta'); dl.replaceChildren();
  if (item.colors?.length) {
    const wrap = node('div', 'colors');
    item.colors.filter((c) => HEX.test(c.hex)).forEach((c) => {
      const b = node('button', 'color-btn'); b.type = 'button';
      const sw = node('i'); sw.style.background = c.hex;
      b.append(sw, document.createTextNode(c.hex));
      b.title = c.name ? `${c.name} — copy` : 'Copy';
      b.addEventListener('click', () => copy(c.hex));
      wrap.append(b);
    });
    row(dl, 'Colors', wrap);
  }
  if (Array.isArray(item.gallery) && item.gallery.length) {
    const strip = node('div', 'gallery');
    item.gallery.forEach((g) => {
      const u = safeUrl(g.file); if (!u) return;
      const a = link('', u, 'gallery-item');
      const im = node('img'); im.src = u; im.alt = g.label || item.name; im.loading = 'lazy'; im.referrerPolicy = 'no-referrer';
      a.append(im); a.title = g.label || '';
      strip.append(a);
    });
    row(dl, 'Stills', strip);
  }
  row(dl, 'Author', item.author);
  row(dl, 'Stack', item.stack);
  row(dl, 'Typefaces', item.fonts);
  row(dl, 'Designers', item.designers);
  row(dl, 'Styles', item.styles);
  row(dl, 'Variable axes', item.axes);
  row(dl, 'Icon set', item.set);
  row(dl, 'Theme', item.theme);
  row(dl, 'Category', item.category || item.section);
  row(dl, 'Platform', item.platform);
  row(dl, 'Tags', (item.tags || []).slice(0, 8));
  if (item.viewport) row(dl, 'Viewport', `${item.viewport.width} × ${item.viewport.height}${item.viewport.mobile ? ' · mobile' : ''}`);
  row(dl, 'Captured', item.capturedAt ? new Date(item.capturedAt).toLocaleString() : null);
  row(dl, 'Checkpoints', item.checkpointCount);
  row(dl, 'Collected', item.collected);
  row(dl, 'Attribution', item.attribution);
  row(dl, 'License', item.license);
  if (safeUrl(item.source)) row(dl, 'Found on', link(domain(item.source) + new URL(safeUrl(item.source)).pathname.slice(0, 48), item.source, ''));

  const links = $('#drawer-links'); links.replaceChildren();
  const open = link('Open original ↗', item.url, 'pill pill--solid'); links.append(open);
  if (item.remix) links.append(link('Remix ↗', item.remix));
  if (item.demo && item.demo !== item.url) links.append(link('Live demo ↗', item.demo));
  if (item.code) links.append(link('Source code ↗', item.code));
  if (item.buildPrompt) links.append(link('Build prompt for agents', item.buildPrompt, 'pill pill--accent'));
  if (item.guide && item.collection === 'showcases') links.append(link('Breakdown', item.guide));
  if (item.svg) links.append(link('SVG ↗', item.svg));
  if (item.cssUrl) { const b = node('button', 'pill', 'Copy CSS link'); b.type = 'button'; b.addEventListener('click', () => copy(item.cssUrl)); links.append(b); }
  if ((item.guide && item.collection !== 'showcases') || item.captureGuide) links.append(link('Capture notes', item.captureGuide || item.guide));
  if (item.record) links.append(link('Evidence JSON', item.record));
  if (item.localDesignPath) links.append(link('Read DESIGN.md', item.localDesignPath));
  const share = node('button', 'pill', 'Copy link'); share.type = 'button';
  share.addEventListener('click', () => copy(item.url));
  links.append(share);

  if (!drawer.open) drawer.showModal();
  drawer.scrollTop = 0;
}
function closeDrawer() { drawer.querySelectorAll('video').forEach((v) => v.pause()); drawer.close(); }
$('#drawer-close').addEventListener('click', closeDrawer);
drawer.addEventListener('click', (e) => { if (e.target === drawer) closeDrawer(); });
drawer.addEventListener('close', () => drawer.querySelectorAll('video').forEach((v) => v.pause()));

/* ── filtering + rendering ───────────────────────────── */
function records() {
  if (state.type === 'all') return Object.keys(COLLECTIONS).flatMap((k) => loaded[k] || []);
  return loaded[state.type] || [];
}
function compute() {
  const words = state.q.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const list = records().filter((it) => (!state.theme || it.theme === state.theme) && words.every((w) => it.searchText.includes(w)));
  if (!words.length && state.type === 'codrops') {
    // lead with entries that have a real preview image; link-only articles go last
    list.sort((a, b) => Number(!!b.preview) - Number(!!a.preview));
  }
  if (words.length) {
    const score = (it) => words.reduce((s, w) => s + (it.nameLower.startsWith(w) ? 3 : it.nameLower.includes(w) ? 2 : 0), 0);
    list.sort((a, b) => score(b) - score(a));
  }
  matching = list;
}
function render({ append = false } = {}) {
  const waiting = state.type === 'all' ? !Object.keys(COLLECTIONS).every((k) => loaded[k]) : !loaded[state.type];
  if (!append) compute();
  const start = append ? grid.querySelectorAll('.card:not(.skeleton)').length : 0;
  const items = matching.slice(start, state.shown);
  const keys = items.map(keyOf).join('\n');
  const needSkeletons = waiting && matching.length < state.shown;
  if (!append && keys && keys === rendered && needSkeletons === !!grid.querySelector('.skeleton')) {
    // a background collection finished loading but the cards on screen are unchanged
    updateStatus(waiting);
    return;
  }
  const slice = items.map((it, i) => cardFor(it, start + i));
  if (append) { grid.querySelectorAll('.skeleton').forEach((s) => s.remove()); grid.append(...slice); rendered += (rendered ? '\n' : '') + keys; }
  else { grid.replaceChildren(...slice); rendered = keys; }
  if (!matching.length && !waiting) {
    const e = node('div', 'empty');
    e.append(node('b', '', 'Nothing on this shelf yet.'), node('p', '', state.q ? `No references match “${state.q}”. Try fewer words or search all collections.` : 'Try another collection.'));
    const reset = node('button', 'pill', 'Search all collections'); reset.type = 'button';
    reset.addEventListener('click', () => { state.type = 'all'; state.theme = ''; sync(); });
    e.append(reset); grid.append(e);
  }
  if (waiting && matching.length < state.shown) grid.append(...skeletons(matching.length ? 3 : 9));
  updateStatus(waiting);
}
let rendered = '';
function updateStatus(waiting) {
  const total = matching.length;
  status.textContent = waiting && !total ? 'Loading…' : `${total.toLocaleString()} result${total === 1 ? '' : 's'}${waiting ? ' · loading more' : ''}`;
  more.hidden = state.shown >= total;
  writeUrl();
}
function writeUrl() {
  const p = new URLSearchParams();
  if (state.q) p.set('q', state.q);
  if (state.type !== 'all') p.set('type', state.type);
  if (state.theme) p.set('theme', state.theme);
  if (state.view !== 'grid') p.set('view', state.view);
  history.replaceState(null, '', location.pathname + (p.size ? '?' + p : ''));
}

/* ── controls ────────────────────────────────────────── */
function buildChips() {
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const mk = (key, label, count, dot) => {
    const b = node('button'); b.type = 'button'; b.setAttribute('role', 'radio'); b.dataset.type = key;
    if (dot) { const d = node('span', 'swatch-dot'); d.style.background = dot; b.append(d); }
    b.append(document.createTextNode(label));
    if (count != null) b.append(node('small', '', count.toLocaleString()));
    b.addEventListener('click', () => { state.type = key; if (key !== 'styles' && key !== 'all') state.theme = ''; sync(); ensure(key); });
    return b;
  };
  const order = Object.keys(COLLECTIONS).sort((a, b) => (a === 'showcases' ? -1 : b === 'showcases' ? 1 : (counts[b] || 0) - (counts[a] || 0)));
  chipsEl.replaceChildren(mk('all', 'Everything', total || null), ...order.map((k) => mk(k, COLLECTIONS[k].label, counts[k], COLLECTIONS[k].dot)));
  $('#total-count').textContent = total.toLocaleString();
}
// When the results change while you're scrolled down, the page gets shorter and the browser
// clamps the scroll position to the new bottom. Bring the top of the results back into view.
function toResults() {
  const toolbar = $('.toolbar');
  // land with the first row just below the sticky toolbar (its `top` is the nav height)
  const stick = toolbar ? toolbar.offsetHeight + (parseFloat(getComputedStyle(toolbar).top) || 0) : 0;
  const top = grid.getBoundingClientRect().top + scrollY - stick - 8;
  if (scrollY > top) scrollTo({ top: Math.max(0, top), behavior: 'instant' });
}
function sync() {
  chipsEl.querySelectorAll('button').forEach((b) => b.setAttribute('aria-checked', String(b.dataset.type === state.type)));
  themesEl.hidden = !(state.type === 'styles' || state.type === 'all');
  themesEl.querySelectorAll('button').forEach((b) => b.setAttribute('aria-checked', String(b.dataset.theme === state.theme)));
  document.querySelectorAll('[data-view]').forEach((b) => { if (b.tagName === 'BUTTON') b.setAttribute('aria-pressed', String(b.dataset.view === state.view)); });
  grid.dataset.view = state.view;
  grid.dataset.type = state.type;
  state.shown = PAGE;
  render();
  toResults();
}
themesEl.addEventListener('click', (e) => { const b = e.target.closest('button'); if (!b) return; state.theme = b.dataset.theme; sync(); });
document.querySelectorAll('.view-toggle button').forEach((b) => b.addEventListener('click', () => { state.view = b.dataset.view; sync(); }));
let typing = 0;
search.addEventListener('input', () => { clearTimeout(typing); typing = setTimeout(() => { state.q = search.value; state.shown = PAGE; render(); }, 120); });
$('#filters').addEventListener('submit', (e) => e.preventDefault());
more.addEventListener('click', () => { state.shown += PAGE; render({ append: true }); });
new IntersectionObserver(([e]) => { if (e.isIntersecting && state.shown < matching.length) { state.shown += PAGE; render({ append: true }); } }, { rootMargin: '600px' }).observe($('#sentinel'));
document.addEventListener('keydown', (e) => {
  const typingInField = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName);
  if ((e.key === '/' && !typingInField) || ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k')) { e.preventDefault(); search.focus(); search.select(); }
  if (e.key === 'Escape' && document.activeElement === search && search.value) { search.value = ''; state.q = ''; render(); }
});

/* theme toggle: per-viewer convenience only */
const themeBtn = $('#theme-toggle');
function applyTheme(t) { if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme; }
try { applyTheme(localStorage.getItem('fl-theme')); } catch { /* storage unavailable */ }
themeBtn.addEventListener('click', () => {
  const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
  const next = dark ? 'light' : 'dark';
  applyTheme(next);
  try { localStorage.setItem('fl-theme', next); } catch { /* ignore */ }
});

/* ── loading ─────────────────────────────────────────── */
const pending = {};
function ensure(kind) {
  if (kind === 'all') return Promise.all(Object.keys(COLLECTIONS).map(ensure));
  if (loaded[kind]) return Promise.resolve();
  if (!pending[kind]) {
    const url = new URL(`data/${COLLECTIONS[kind].file}`, BASE);
    const attempt = () => fetch(url).then((r) => { if (!r.ok) throw new Error(`Could not load ${COLLECTIONS[kind].file} (${r.status})`); return r.json(); });
    // one retry: a single network hiccup shouldn't take the whole viewer down
    pending[kind] = attempt().catch(() => new Promise((res) => setTimeout(res, 900)).then(attempt))
      .then((data) => {
        loaded[kind] = data.items.map((it) => ({ ...it, collection: kind, nameLower: String(it.name || '').toLowerCase(), searchText: JSON.stringify(it).toLowerCase() }));
        if (state.type === kind || state.type === 'all') render();
      });
  }
  return pending[kind];
}

async function init() {
  const p = new URLSearchParams(location.search);
  state.q = p.get('q') || '';
  search.value = state.q;
  const t = p.get('type');
  if (t === 'all' || COLLECTIONS[t]) state.type = t;
  if (['dark', 'light', 'mixed'].includes(p.get('theme'))) state.theme = p.get('theme');
  if (p.get('view') === 'list') state.view = 'list';
  try {
    const manifest = await (await fetch(new URL('data/library-manifest.json', BASE))).json();
    for (const c of manifest.collections) if (COLLECTIONS[c.name]) counts[c.name] = c.count;
  } catch { /* chips still work without counts */ }
  buildChips();
  sync();
  // the chosen collection first, then the rest one at a time so the page stays responsive
  const first = state.type === 'all' ? 'captures' : state.type;
  await ensure(first);
  for (const k of Object.keys(COLLECTIONS)) { if (k !== first) await ensure(k); }
}
init().catch((err) => {
  status.textContent = 'Collection unavailable';
  const m = $('#error'); m.hidden = false;
  m.textContent = `${err.message}. Serve the repository with “python3 -m http.server 8000” and open http://localhost:8000/library/.`;
  grid.querySelectorAll('.skeleton').forEach((s) => s.remove());
});

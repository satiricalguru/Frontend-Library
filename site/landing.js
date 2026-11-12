/* Frontend Library — landing page behaviour.
 * Motion (motion.dev) drives scroll-linked and in-view animation; site/scene.js renders the
 * Three.js hero. All external catalog text is inserted with DOM APIs (textContent), never HTML.
 */
import { animate, scroll, inView, stagger } from 'motion';
// note: Motion 11's inView callback receives an IntersectionObserverEntry (use entry.target)

const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const root = document.documentElement;
root.classList.add(reduced ? 'reduced' : 'motion-ok');
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const fmt = (n) => n.toLocaleString('en-US');
function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
async function json(path) { const r = await fetch(path); if (!r.ok) throw new Error(`${path}: ${r.status}`); return r.json(); }

const META = {
  styles: ['Brand design systems', 'Refero Styles', 'swatch'],
  fonts: ['Award fonts', 'Envato Elements', 'type'],
  motion: ['Motion examples', 'motion.dev', 'gif:split-text-reveal'],
  godly: ['Websites & templates', 'Godly', 'text'],
  codrops: ['WebGL demos & articles', 'Codrops', 'text'],
  'media-resources': ['Media & design resources', 'Curated lists', 'text'],
  'design-md': ['DESIGN.md analyses', 'awesome-design-md', 'text'],
  captures: ['Captured landing pages', 'Lusion · recorded', 'capture'],
  transitions: ['UI micro-transitions', 'transitions.dev', 'gif:sliding-tabs'],
  lusion: ['3D case studies & labs', 'Lusion', 'capture'],
  'google-fonts': ['Open-source font families', 'Google Fonts', 'type'],
  threejs: ['Three.js examples', 'threejs.org', 'text'],
  icons: ['Open icon sets', 'Lucide · Tabler', 'text'],
};

/* ── 0. nav backdrop once the page scrolls ──────────────────── */
const nav = $('.nav');
const onScroll = () => nav.classList.toggle('is-scrolled', scrollY > 40);
addEventListener('scroll', onScroll, { passive: true }); onScroll();

/* ── 1. hero scene ─────────────────────────────────────────── */
const track = $('#hero');
const stage = $('.stage');
const canvas = $('.stage-canvas');
const heroCopy = $('.hero-copy');
const bar = $('.progress-bar');
const label = $('[data-progress-label]');
let shelf = null;

function webglOK() {
  try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); } catch { return false; }
}

async function initScene() {
  if (!webglOK()) return;
  try {
    const { createShelf } = await import('./scene.js');
    shelf = createShelf(canvas, { count: innerWidth < 720 ? 720 : 1342, reduced });
    stage.classList.add('is-webgl');
    if (reduced) { shelf.setProgress(0.5); return; }
    const io = new IntersectionObserver(([e]) => (e.isIntersecting ? shelf.start() : shelf.stop()), { rootMargin: '100px' });
    io.observe(track);
    stage.addEventListener('pointermove', (e) => {
      const r = stage.getBoundingClientRect();
      shelf.setPointer(((e.clientX - r.left) / r.width - 0.5) * 2, -((e.clientY - r.top) / r.height - 0.5) * 2);
    });
    stage.addEventListener('pointerleave', () => shelf.setPointer(0, 0));
  } catch (err) {
    console.warn('Hero scene unavailable, showing the static stage.', err);
  }
}

/* Kinetic type. Every word gets its own scroll window: it spawns (rise + unblur + tracking in)
 * and later dissolves (rise out + blur + tracking out), staggered by word order, so lines build
 * and break apart in step with the WebGL scene driven by the same progress value. */
const smooth = (t) => t * t * (3 - 2 * t);
const win = (p, a, b) => smooth(clamp((p - a) / (b - a)));
function splitWords(el) {
  const words = [];
  const walk = (n) => [...n.childNodes].forEach((c) => {
    if (c.nodeType === 3) {
      const frag = document.createDocumentFragment();
      c.textContent.split(/(\s+)/).forEach((part) => {
        if (!part) return;
        if (/^\s+$/.test(part)) { frag.append(part); return; }
        const w = document.createElement('span'); w.className = 'kw'; w.textContent = part; frag.append(w); words.push(w);
      });
      c.replaceWith(frag);
    } else walk(c);
  });
  walk(el);
  return words;
}
function paintWord(w, enter, exit) {
  const v = enter * (1 - exit);
  w.style.opacity = v.toFixed(3);
  w.style.filter = v > 0.995 ? '' : `blur(${((1 - v) * 14).toFixed(1)}px)`;
  w.style.transform = `translate3d(0, ${((1 - enter) * 0.55 - exit * 0.5).toFixed(3)}em, 0) scale(${(0.92 + 0.08 * enter + 0.06 * exit).toFixed(3)})`;
  w.style.letterSpacing = `${((1 - v) * 0.12).toFixed(3)}em`;
}
// headline: already on screen; its words dissolve between 4% and 28% of the hero scroll
const titleWords = splitWords($('.hero-title'));
const extras = [...heroCopy.querySelectorAll('.eyebrow, .hero-sub, .hero-actions')];
// scene lines: words spawn over the first part of their range and dissolve near its end
const lines = $$('.k-line').map((line) => {
  const [a, b] = line.dataset.range.split(' ').map(Number);
  const words = splitWords(line.querySelector('.k-words'));
  return { line, a, b, words, tag: line.querySelector('.k-tag'), sub: line.querySelector('.k-sub') };
});

function heroProgress(p) {
  shelf?.setProgress(p);
  const n = titleWords.length;
  titleWords.forEach((w, i) => { const s = 0.04 + (i / n) * 0.16; paintWord(w, 1, win(p, s, s + 0.08)); });
  const extraFade = win(p, 0.02, 0.1);
  extras.forEach((e) => { e.style.opacity = String(1 - extraFade); e.style.transform = `translateY(${-extraFade * 24}px)`; });
  heroCopy.style.visibility = p > 0.3 ? 'hidden' : 'visible';
  heroCopy.style.pointerEvents = extraFade > 0.6 ? 'none' : '';
  for (const ln of lines) {
    const span = ln.b - ln.a, m = ln.words.length;
    const last = ln.b > 1;
    ln.words.forEach((w, i) => {
      const es = ln.a + (i / m) * span * 0.3, xs = ln.b - span * 0.25 + (i / m) * span * 0.18;
      paintWord(w, win(p, es, es + span * 0.12), last ? 0 : win(p, xs, xs + span * 0.08));
    });
    const tagV = win(p, ln.a, ln.a + span * 0.1) * (last ? 1 : 1 - win(p, ln.b - span * 0.12, ln.b));
    ln.tag.style.opacity = tagV.toFixed(3);
    if (ln.sub) ln.sub.style.opacity = win(p, ln.a + span * 0.35, ln.a + span * 0.5).toFixed(3);
    ln.line.style.visibility = p > ln.a - 0.02 && (last || p < ln.b + 0.02) ? 'visible' : 'hidden';
  }
  bar.style.transform = `scaleX(${p})`;
  label.textContent = String(Math.round(p * 100)).padStart(3, '0');
}

if (!reduced) {
  scroll(heroProgress, { target: track, offset: ['start start', 'end end'] });
  animate('.hero-title .line > span', { y: ['110%', '0%'] }, { duration: 1.1, delay: stagger(0.09, { startDelay: 0.15 }), ease: [0.16, 1, 0.3, 1] });
  animate('.hero-sub, .hero-actions, .hero-copy .eyebrow', { opacity: [0, 1], y: [16, 0] }, { duration: 0.9, delay: stagger(0.08, { startDelay: 0.5 }), ease: [0.16, 1, 0.3, 1] });
} else {
  heroProgress(0);
}
initScene();

/* ── 2. reveals ────────────────────────────────────────────── */
if (!reduced) {
  inView('[data-reveal]', (info) => { animate(info.target || info, { opacity: 1, y: 0 }, { duration: 0.9, ease: [0.16, 1, 0.3, 1] }); }, { amount: 0.3 });
  inView('.snippet-grid', (info) => { animate((info.target || info).children, { opacity: [0, 1], y: [40, 0] }, { duration: 0.8, delay: stagger(0.06), ease: [0.16, 1, 0.3, 1] }); }, { amount: 0.15 });
}

/* ── 3. counts + index rows (from the manifest) ────────────── */
const preview = $('.index-preview');
const previewInner = $('.index-preview-inner');
let paletteHexes = [];
let captureImages = [];

function renderPreview(kind) {
  previewInner.replaceChildren();
  if (kind === 'swatch' && paletteHexes.length) {
    const g = el('div', 'preview-swatches');
    for (let i = 0; i < 16; i++) { const s = el('span'); s.style.background = paletteHexes[(i * 37) % paletteHexes.length]; g.append(s); }
    previewInner.append(g);
  } else if (kind === 'capture' && captureImages.length) {
    const img = el('img'); img.alt = ''; img.src = captureImages[Math.floor(Math.random() * captureImages.length)];
    previewInner.append(img);
  } else if (kind?.startsWith('gif:')) {
    const img = el('img'); img.alt = ''; img.src = `.github/assets/gifs/${kind.slice(4)}.gif`;
    previewInner.append(img);
  } else if (kind === 'type') {
    const t = el('div', 'preview-type serif', 'Aa Award'); previewInner.append(t);
  } else {
    preview.classList.remove('is-on');
    return false;
  }
  return true;
}

async function initIndex() {
  const manifest = await json('data/library-manifest.json');
  const cols = manifest.collections;
  const total = cols.reduce((a, c) => a + c.count, 0);
  const byName = Object.fromEntries(cols.map((c) => [c.name, c.count]));
  $$('[data-count]').forEach((n) => {
    const k = n.dataset.count;
    const v = k === 'total' ? total : byName[k];
    if (v != null) n.textContent = fmt(v);
  });
  const list = $('#index-list');
  const rows = [...cols].sort((a, b) => b.count - a.count).map((c, i) => {
    const [name, src, kind] = META[c.name] || [c.name, '', 'text'];
    const li = el('li');
    const a = el('a'); a.href = `library/?type=${encodeURIComponent(c.name)}`; a.dataset.preview = kind;
    a.append(el('span', 'idx', String(i + 1).padStart(2, '0')), el('span', 'name', name), el('span', 'src', src), el('span', 'num', fmt(c.count)));
    li.append(a);
    return li;
  });
  list.replaceChildren(...rows);
  if (!reduced) inView(list, () => { animate(list.children, { opacity: [0, 1], y: [24, 0] }, { duration: 0.7, delay: stagger(0.05), ease: [0.16, 1, 0.3, 1] }); });

  let px = 0, py = 0, x = 0, y = 0, raf = 0;
  const follow = () => { x += (px - x) * 0.18; y += (py - y) * 0.18; preview.style.left = x + 24 + 150 + 'px'; preview.style.top = y + 'px'; raf = requestAnimationFrame(follow); };
  list.addEventListener('pointerover', (e) => {
    const a = e.target.closest('a'); if (!a) return;
    if (renderPreview(a.dataset.preview)) { preview.classList.add('is-on'); if (!raf) { x = px; y = py; follow(); } }
  });
  list.addEventListener('pointermove', (e) => { px = e.clientX; py = e.clientY; });
  list.addEventListener('pointerleave', () => { preview.classList.remove('is-on'); cancelAnimationFrame(raf); raf = 0; });
}
initIndex().catch((e) => console.warn('Index counts unavailable', e));

/* ── 4. captures rail ──────────────────────────────────────── */
async function initCaptures() {
  const data = await json('data/landing-pages.json');
  const seen = new Set();
  const items = data.items.filter((it) => it.status === 'captured' && it.preview && !it.viewport?.mobile && !seen.has(it.preview) && seen.add(it.preview)).slice(0, 14);
  captureImages = items.map((it) => it.preview);
  const rail = $('#captures-rail');
  rail.replaceChildren(...items.map((it) => {
    const a = el('a', 'capture-card');
    a.href = `library/?type=captures&q=${encodeURIComponent(it.name)}`;
    const fig = el('figure');
    const img = el('img'); img.src = it.preview; img.alt = `Captured viewport of ${it.name}`; img.loading = 'lazy'; img.decoding = 'async';
    img.addEventListener('error', () => a.remove(), { once: true });
    fig.append(img);
    const p = el('p'); p.append(el('span', '', it.name.replace(/ — live experience$/, '')), el('small', '', (it.kind || '').replace(/-/g, ' ')));
    a.append(fig, p);
    return a;
  }));
  if (reduced) return;
  scroll((p) => {
    const max = rail.scrollWidth - innerWidth;
    rail.style.transform = `translate3d(${-max * clamp((p - 0.1) / 0.85)}px,0,0)`;
  }, { target: $('#captures'), offset: ['start start', 'end end'] });
}
initCaptures().catch((e) => console.warn('Captures unavailable', e));

/* ── 5. palettes (also recolors the hero scene) ────────────── */
function lum(hex) {
  let h = hex.replace('#', ''); if (h.length === 3) h = [...h].map((c) => c + c).join('');
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
const contrast = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05); };
const HEX = /^#[0-9a-f]{3}([0-9a-f]{3})?$/i;
let styles = [];

function tilePair(s) {
  const cs = s.colors.map((c) => c.hex).filter((h) => HEX.test(h));
  let best = [0, cs[0], cs[1]];
  for (const a of cs) for (const b of cs) if (a !== b) { const c = contrast(a, b); if (c > best[0]) best = [c, a, b]; }
  let [score, bg, fg] = best;
  if (score < 4.5) { bg = cs.reduce((m, c) => (Math.abs(lum(c) - 0.18) > Math.abs(lum(m) - 0.18) ? c : m), cs[0]); fg = contrast(bg, '#ffffff') > contrast(bg, '#0a0b10') ? '#ffffff' : '#0a0b10'; }
  return [bg, fg, cs];
}

function sat(hex) {
  let h = hex.replace('#', ''); if (h.length === 3) h = [...h].map((c) => c + c).join('');
  const v = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
  const mx = Math.max(...v), mn = Math.min(...v);
  return mx === 0 ? 0 : (mx - mn) / mx;
}
function renderPalettes() {
  const grid = $('#palette-grid');
  const n = innerWidth < 520 ? 6 : 12;
  // favour palettes with at least one saturated color, so the grid isn't all greyscale
  const vivid = styles.filter((s) => s.colors.some((c) => HEX.test(c.hex) && sat(c.hex) > 0.45));
  const pool = vivid.length > 40 ? vivid : styles;
  const pick = [...pool].sort(() => Math.random() - 0.5).slice(0, n);
  grid.replaceChildren(...pick.map((s) => {
    const [bg, fg, cs] = tilePair(s);
    const b = el('button', 'palette-tile'); b.type = 'button';
    b.style.background = bg; b.style.color = fg;
    const chips = el('span', 'chips'); cs.slice(0, 4).forEach((h) => { const i = el('i'); i.style.background = h; chips.append(i); });
    b.append(chips, el('b', '', s.name), el('small', '', cs.slice(0, 2).join(' · ')));
    b.setAttribute('aria-label', `Copy ${s.name} colors ${cs.slice(0, 2).join(' and ')}`);
    b.addEventListener('click', async () => {
      const text = `${s.name}: ${cs.join(' ')}`;
      try { await navigator.clipboard.writeText(text); toast(`Copied ${cs.slice(0, 2).join(' / ')}`); } catch { toast(text); }
    });
    return b;
  }));
  if (!reduced) animate(grid.children, { opacity: [0, 1], scale: [0.92, 1] }, { duration: 0.6, delay: stagger(0.035), ease: [0.34, 1.56, 0.64, 1] });
}
let toastTimer = 0;
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('is-on'); clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove('is-on'), 1800); }
$('#shuffle').addEventListener('click', renderPalettes);

async function initPalettes() {
  const data = await json('data/refero-styles.json');
  styles = data.items.filter((s) => s.colors?.length >= 2);
  paletteHexes = styles.flatMap((s) => s.colors.slice(0, 2).map((c) => c.hex)).filter((h) => HEX.test(h));
  shelf?.setPalette(paletteHexes);
  renderPalettes();
}
const idle = window.requestIdleCallback || ((f) => setTimeout(f, 600));
idle(() => initPalettes().catch((e) => console.warn('Palettes unavailable', e)));
// the scene may finish loading after the palettes
const wait = setInterval(() => { if (shelf && paletteHexes.length) { shelf.setPalette(paletteHexes); clearInterval(wait); } }, 400);
setTimeout(() => clearInterval(wait), 20000);

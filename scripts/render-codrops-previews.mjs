#!/usr/bin/env node
/**
 * Render real preview screenshots for Codrops demo repositories that have no usable image.
 *
 *   node scripts/render-codrops-previews.mjs [--all] [--limit N] [--repo Name[,Name]] [--min-bytes 14000]
 *
 * For each selected item in data/codrops-webgl.json (default: previewSource "github-social-card"):
 *   1. shallow-clone the official github.com/codrops repository (no hooks, no npm install, no build),
 *   2. serve its static files from a local loopback server,
 *   3. open the demo's index.html in headless Chrome with every tympanus.net / Codrops CDN request
 *      blocked (Codrops restricts AI crawlers there; see data/source-policies.json),
 *   4. save a 960px JPEG to captures/codrops-renders/<repo>.jpg and record provenance on the item.
 * Pages that render blank (unbuilt sources, missing assets) are left on their previous preview.
 * Requires Node 22+, Chrome/Chromium and ffmpeg. The screenshot is reference evidence only:
 * the demo's code, images and fonts remain the property of Codrops and the demo authors.
 */
import { createServer } from 'node:http';
import { execFileSync } from 'node:child_process';
import { mkdtemp, rm, readFile, writeFile, mkdir, stat, access } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve, extname, normalize, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launchBrowser, pause } from './lib/browser.mjs';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const DATA = join(ROOT, 'data/codrops-webgl.json');
const OUT = join(ROOT, 'captures/codrops-renders');
const args = process.argv.slice(2);
const opt = (name) => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
const BLOCK = ['*://tympanus.net/*', '*://*.tympanus.net/*', '*://*.netdna-cdn.com/*', '*://*.stackpathcdn.com/*', '*://*.kxcdn.com/*'];
const ENTRIES = ['index.html', 'dist/index.html', 'docs/index.html', 'build/index.html', 'public/index.html', 'demo/index.html', 'index2.html'];
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webp': 'image/webp',
  '.avif': 'image/avif', '.mp4': 'video/mp4', '.webm': 'video/webm', '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttf': 'font/ttf',
  '.otf': 'font/otf', '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.wasm': 'application/wasm', '.hdr': 'application/octet-stream' };

const catalog = JSON.parse(await readFile(DATA, 'utf8'));
let items = catalog.items.filter((it) => /github\.com\/codrops\//i.test(it.url) &&
  (args.includes('--all') ? !it.preview || it.previewSource === 'github-social-card' : it.previewSource === 'github-social-card'));
if (opt('--repo')) { const want = opt('--repo').toLowerCase().split(','); items = items.filter((it) => want.includes(it.url.split('/').pop().toLowerCase())); }
const MIN_BYTES = Number(opt('--min-bytes') || 14000);
if (opt('--limit')) items = items.slice(0, Number(opt('--limit')));
console.log(`rendering ${items.length} repositories`);
await mkdir(OUT, { recursive: true });

// one loopback server whose document root is switched per repository
let docRoot = null;
const server = createServer(async (req, res) => {
  try {
    const path = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let file = normalize(join(docRoot, path));
    if (!docRoot || !(file + sep).startsWith(docRoot + sep) && file !== docRoot) { res.writeHead(403).end(); return; }
    if ((await stat(file)).isDirectory()) file = join(file, 'index.html');
    res.writeHead(200, { 'Content-Type': TYPES[extname(file).toLowerCase()] || 'application/octet-stream' });
    res.end(await readFile(file));
  } catch { res.writeHead(404).end(); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const browser = await launchBrowser();
await browser.send('Network.setBlockedURLs', { urls: BLOCK });
await browser.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false });
const results = { rendered: 0, blank: 0, noEntry: 0, cloneFailed: 0 };

try {
  for (const item of items) {
    const repo = item.url.split('/').pop();
    const work = await mkdtemp(join(tmpdir(), 'codrops-'));
    try {
      try {
        execFileSync('git', ['clone', '--depth', '1', '--quiet', '--no-tags', `https://github.com/codrops/${repo}.git`, work + '/src'],
          { timeout: 180000, stdio: 'ignore', env: { ...process.env, GIT_TERMINAL_PROMPT: '0' } });
      } catch { results.cloneFailed++; console.log(`clone failed  ${repo}`); continue; }
      const src = join(work, 'src');
      const sha = execFileSync('git', ['-C', src, 'rev-parse', 'HEAD']).toString().trim();
      let entry = null;
      for (const e of ENTRIES) { try { await access(join(src, e)); entry = e; break; } catch { /* next */ } }
      if (!entry) { results.noEntry++; console.log(`no entry      ${repo}`); continue; }
      docRoot = resolve(src);
      await browser.send('Page.navigate', { url: `http://127.0.0.1:${port}/${entry}` });
      for (let i = 0; i < 40; i++) { if (await browser.evaluate('document.readyState') === 'complete') break; await pause(250); }
      await pause(3500);
      await browser.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: 760, y: 380 });
      await pause(700);
      const facts = await browser.evaluate(`(() => {
        const vis = [...document.querySelectorAll('img,canvas,video,svg,h1,h2,h3,p,a')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 20 && r.bottom > 0 && r.top < innerHeight; });
        return { visible: vis.length, text: (document.body?.innerText || '').trim().length, canvas: document.querySelectorAll('canvas').length };
      })()`).catch(() => ({ visible: 0, text: 0, canvas: 0 }));
      const shot = await browser.send('Page.captureScreenshot', { format: 'jpeg', quality: 82 });
      const raw = join(work, 'shot.jpg');
      await writeFile(raw, Buffer.from(shot.data, 'base64'));
      const out = join(OUT, `${repo}.jpg`);
      execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', raw, '-vf', 'scale=960:-2', '-q:v', '4', out]);
      const bytes = (await stat(out)).size;
      // near-uniform frames compress to almost nothing; treat them (and empty DOMs) as failed renders
      if (bytes < MIN_BYTES || (facts.visible === 0 && facts.canvas === 0)) {
        await rm(out, { force: true });
        results.blank++; console.log(`blank         ${repo} (${bytes} B, ${facts.visible} visible)`);
        continue;
      }
      item.previewSocialCard = item.previewSocialCard || (item.previewSource === 'github-social-card' ? item.preview : undefined);
      item.preview = `captures/codrops-renders/${repo}.jpg`;
      item.previewSource = 'local-render';
      item.previewCommit = sha;
      item.previewEntry = entry;
      item.previewNote = 'Rendered locally in headless Chrome (1280x800) from the official repository at previewCommit; tympanus.net and Codrops CDN requests blocked. Reference screenshot only; the demo and its assets belong to Codrops and the demo authors.';
      delete item.previewHost;
      results.rendered++; console.log(`rendered      ${repo} (${Math.round(bytes / 1024)} KB)`);
    } catch (error) {
      results.blank++; console.log(`error         ${repo}: ${error.message}`);
    } finally {
      await rm(work, { recursive: true, force: true, maxRetries: 3 });
    }
  }
} finally {
  await browser.close();
  server.close();
}

const counts = {};
for (const it of catalog.items) if (it.previewSource) counts[it.previewSource] = (counts[it.previewSource] || 0) + 1;
if (catalog.coverage) catalog.coverage.previews = { ...(catalog.coverage.previews || {}), bySource: counts, localRenders: counts['local-render'] || 0 };
await writeFile(DATA, JSON.stringify(catalog, null, 2) + '\n');
console.log(JSON.stringify({ ...results, previewSources: counts }));

/* Live GitHub star count for every [data-stars] button.
 * Reads the public GitHub REST API (no token, 60 requests/hour per visitor), caches the value
 * for 30 minutes in localStorage as a per-viewer convenience, and counts up when it arrives.
 * If the API is unreachable or rate-limited the button still works and simply shows "Star". */
(() => {
  'use strict';
  const buttons = [...document.querySelectorAll('[data-stars]')];
  if (!buttons.length) return;
  const API = 'https://api.github.com/repos/satiricalguru/Frontend-Library';
  const KEY = 'fl-stars-v1';
  const TTL = 30 * 60 * 1000;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fmt = (n) => (n >= 10000 ? `${(n / 1000).toFixed(0)}k` : n >= 1000 ? `${(n / 1000).toFixed(1).replace(/\.0$/, '')}k` : String(n));

  function show(n, animate) {
    for (const b of buttons) {
      const out = b.querySelector('[data-star-count]');
      b.classList.remove('is-loading');
      b.setAttribute('aria-label', `Star Frontend Library on GitHub — ${n.toLocaleString('en-US')} stars`);
      if (!animate || reduced || n < 2) { out.textContent = fmt(n); continue; }
      const start = performance.now(), dur = 900;
      const tick = (t) => {
        const k = Math.min(1, (t - start) / dur), e = 1 - Math.pow(1 - k, 3);
        out.textContent = fmt(Math.round(n * e));
        if (k < 1) requestAnimationFrame(tick); else { b.classList.add('is-bump'); setTimeout(() => b.classList.remove('is-bump'), 700); }
      };
      requestAnimationFrame(tick);
    }
  }
  function hideCount() { for (const b of buttons) { const c = b.querySelector('[data-star-count]'); if (c) c.hidden = true; b.classList.remove('is-loading'); } }

  let cached = null;
  try { cached = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch { /* storage unavailable */ }
  if (cached && typeof cached.n === 'number') show(cached.n, false);
  else buttons.forEach((b) => b.classList.add('is-loading'));
  if (cached && Date.now() - cached.t < TTL) return;

  fetch(API, { headers: { Accept: 'application/vnd.github+json' } })
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
    .then((d) => {
      const n = Number(d.stargazers_count);
      if (!Number.isFinite(n)) throw new Error('no count');
      try { localStorage.setItem(KEY, JSON.stringify({ n, t: Date.now() })); } catch { /* ignore */ }
      show(n, !cached || cached.n !== n);
    })
    .catch(() => { if (!cached) hideCount(); });
})();

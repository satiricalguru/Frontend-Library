/* Shared footer: giant wordmark split into letters that rise in when the footer enters the
 * viewport and follow the pointer with a magnetic lean; live reference count from the manifest. */
(() => {
  'use strict';
  const footer = document.querySelector('[data-footer]');
  if (!footer) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const base = new URL('../', document.currentScript.src); // footer.js lives in /site/

  // split the giant wordmark into letters (aria-hidden; the link has an aria-label)
  const target = footer.querySelector('[data-split]');
  const letters = [];
  [...target.textContent].forEach((ch, i) => {
    const s = document.createElement('span');
    s.className = ch === ' ' ? 'sp' : 'ch';
    s.textContent = ch === ' ' ? ' ' : ch;
    s.style.setProperty('--i', String(i));
    if (ch !== ' ') letters.push(s);
    target.append(s);
  });
  target.firstChild.remove(); // the original text node

  // fit the wordmark to the footer width (Syne is wide; vw sizing alone overflows)
  const giantLink = footer.querySelector('.sf-giant');
  const fit = () => {
    giantLink.style.fontSize = '100px';
    const w = target.scrollWidth, avail = giantLink.clientWidth;
    if (w && avail) giantLink.style.fontSize = `${Math.floor((100 * avail) / w * 0.985)}px`;
  };
  fit();
  if (document.fonts?.ready) document.fonts.ready.then(fit);
  new ResizeObserver(fit).observe(footer);

  if (reduced || !('IntersectionObserver' in window)) footer.classList.add('is-in');
  else {
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { footer.classList.add('is-in'); io.disconnect(); } }, { threshold: 0.2 });
    io.observe(footer);
  }

  // magnetic lean: letters near the pointer lift and tilt toward it
  const giant = footer.querySelector('.sf-giant');
  if (!reduced && matchMedia('(hover: hover)').matches) {
    let raf = 0, px = -9999;
    const paint = () => {
      raf = 0;
      for (const l of letters) {
        const r = l.getBoundingClientRect();
        const d = (px - (r.left + r.width / 2)) / r.width;
        const f = Math.max(0, 1 - Math.abs(d) / 3);
        l.style.setProperty('--lift', `${(-f * 0.12).toFixed(3)}em`);
        l.style.setProperty('--tilt', `${(d * f * -6).toFixed(2)}deg`);
      }
    };
    giant.addEventListener('pointermove', (e) => { px = e.clientX; if (!raf) raf = requestAnimationFrame(paint); });
    giant.addEventListener('pointerleave', () => { px = -9999; if (!raf) raf = requestAnimationFrame(paint); });
  }

  // live count
  fetch(new URL('data/library-manifest.json', base))
    .then((r) => (r.ok ? r.json() : null))
    .then((m) => {
      if (!m) return;
      const total = m.collections.reduce((a, c) => a + c.count, 0);
      footer.querySelectorAll('[data-footer-count]').forEach((n) => { n.textContent = total.toLocaleString('en-US'); });
    })
    .catch(() => {});
})();

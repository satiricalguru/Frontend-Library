# GitHub Copilot Instructions — Frontend Library

This repository is a curated, source-tracked frontend library containing catalog indexes (`data/*.json`), self-contained HTML/CSS/JS animations (`animations/snippets/`), UI components (`components/`), design system palettes (`styles/`), and build/validation scripts (`scripts/`).

## Code Review & Contribution Checklist

When reviewing Pull Requests or preparing changes for merge:

1. **No Direct Pushes / Clean Scope**
   - Ensure changes are scoped to the asset, documentation, or script being added or fixed.
   - Reject committed build artifacts (`node_modules/`, `dist/`, `build/`, `out/`), OS clutter (`.DS_Store`, `Thumbs.db`), `.env` files, or secrets/tokens.

2. **Folder & Naming Conventions**
   - Snippet and component directories under `animations/snippets/<name>/` and `components/<name>/` (except `_shared`) must use lowercase `kebab-case` and contain an `index.html`.
   - Third-party paid/copyrighted assets must never be committed; link to original sources instead.

3. **HTML, CSS, JS & Accessibility Quality**
   - Every `index.html` snippet must include `<!doctype html>`, `<html lang="...">`, `<meta charset="utf-8">`, `<meta name="viewport" ...>`, and a descriptive `<title>`.
   - Animations and transitions must respect `@media (prefers-reduced-motion: reduce)`.
   - Interactive controls must support keyboard navigation, visible focus (`:focus-visible`), and proper ARIA attributes (`aria-expanded`, `aria-selected`, `aria-label`, etc.).
   - Flag unsafe DOM patterns (`eval()`, `new Function()`, `document.write()`, or unsanitized `innerHTML` with user-controlled strings) and broken relative `href`/`src` paths.

4. **Catalog Data & Generated Files**
   - Entries in `data/*.json` must include `name`, `url`, `source`, and an accurate `count`.
   - If `data/*.json` or `animations/snippets/SOURCES.json` changed, verify `python3 scripts/build-catalog.py`, `python3 scripts/build-visuals.py`, `python3 scripts/validate-data.py`, and `node scripts/check-code.mjs` were run and generated files are committed.

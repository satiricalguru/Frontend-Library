# Contributing to Frontend Library

Thanks for your interest in contributing to **Frontend Library**! Contributions of reusable frontend assets, improvements, bug fixes, and documentation updates are welcome via Pull Requests.

## What You Can Contribute

- **Animations (`animations/`)**: CSS keyframes, Lottie JSONs, GSAP/Framer Motion presets, and micro-interactions.
- **Components (`components/`)**: Reusable UI components, cards, modals, navbars, forms, and layout snippets.
- **Fonts (`fonts/`)**: Open-source webfonts and typography kits with license details.
- **Icons (`icons/`)**: Clean SVG icons and icon packs.
- **Images (`images/`)**: Textures, gradients, backgrounds, illustrations, and placeholder media.
- **Styles (`styles/`)**: CSS/SCSS utilities, design tokens, themes, and reset/base sheets.
- **Templates (`templates/`)**: Starter layouts and boilerplate pages.
- **Inspiration (`inspiration/`)**: Curated links to standout websites and creative-tech work.
- **Catalog entries (`data/*.json`)**: Linked resources from third-party sites. Every entry **must** include the item `url` and the exact `source` page you found it on. Run `python3 scripts/build-catalog.py` afterwards so the Markdown catalogs, `SOURCES.md` and `data/sources.csv` stay in sync. Never commit third-party files (fonts, paid assets, copied code); link to them instead.

## Asset Guidelines

1. **Choose the right folder**: Place each contribution inside the matching top-level category directory above.
2. **Use kebab-case naming**: Name files and subfolders clearly in lowercase kebab-case (for example, `components/glassmorphic-card/`).
3. **Keep assets self-contained**: Group multi-file assets (HTML/CSS/JS, usage notes, previews) in their own subfolder and avoid committing `node_modules/`, build outputs, or secrets.
4. **Verify licensing & attribution**: Submit only original work or assets under permissive open-source/free-to-share licenses, and include license or attribution details in a short `README.md` inside the asset subfolder when applicable.
5. **Document & preview**: When submitting visual components, animations, or templates, include a brief usage note and attach a screenshot or short preview in your Pull Request.

## Pull Request Workflow

1. **Fork** the repository to your GitHub account.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/Frontend-Library.git
   cd Frontend-Library
   ```
3. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/add-asset-name
   ```
4. **Add your changes**, verify they work cleanly, and commit with a clear message:
   ```bash
   git add .
   git commit -m "feat(components): add glassmorphic card"
   ```
5. **Push** your branch to your fork:
   ```bash
   git push origin feat/add-asset-name
   ```
6. **Open a Pull Request** against `main` on GitHub and fill out the PR template checklist.

## Preview GIFs

Animated previews are captured from the demo page with headless Chrome, so the GIF always matches the code you shipped. The script needs Node 18+ (for the built-in `WebSocket`), Chrome or Chromium, and `ffmpeg` on your `PATH`:

```bash
node scripts/capture-gif.mjs animations/snippets/<name>/index.html .github/assets/gifs/<name>.gif
```

The optional arguments are the capture length in milliseconds and the frame rate:

```bash
node scripts/capture-gif.mjs components/<name>/index.html .github/assets/gifs/<name>.gif 2600 20
```

Set `GIF_WIDTH` and `GIF_HEIGHT` to change the capture viewport when a component is taller than the default stage.

## Checks that run on your PR

Direct pushes to `main` are disabled for everyone (including collaborators) — all changes must be submitted via a Pull Request and approved before merge. Automated CI and code-checking bots (catalog validation, HTML/CSS/JS hygiene, Ruff, `actionlint`, CodeQL, Dependency Review, PR Auto-Labeler, and GitHub Copilot Code Review) run on every PR.

Run the local checks before pushing:

```bash
python3 scripts/build-catalog.py && python3 scripts/build-visuals.py
python3 scripts/validate-data.py
node scripts/check-code.mjs
git diff --exit-code   # should print nothing
```

## Need Help or Have Ideas?

Open an Issue to suggest a new asset category, report a broken asset, or discuss changes before submitting a large PR.


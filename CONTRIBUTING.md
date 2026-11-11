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

## Need Help or Have Ideas?

Open an Issue to suggest a new asset category, report a broken asset, or discuss changes before submitting a large PR.

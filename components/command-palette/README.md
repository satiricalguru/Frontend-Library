# Command palette

A filterable ⌘K palette with keyboard navigation. No dependencies, no build step —
one HTML file plus about 100 lines of CSS and JS.

Open [`index.html`](index.html) in a browser to see it working.

## What you get

| Part | What it does |
|:--|:--|
| `commandPalette(root, commands)` | Wires up a root element and a list of `{ label, hint, action }` commands |
| `⌘K` / `Ctrl+K` | Opens the palette from anywhere on the page |
| `↑` `↓` | Move the selection |
| `↵` | Run the selected command |
| `esc` | Close the palette |

## Usage

```html
<div class="palette" id="palette">
  <button class="palette__btn" id="paletteBtn">Search…</button>
  <div class="palette__panel">
    <div class="palette__search"><input class="palette__input" id="paletteInput" type="text"></div>
    <ul class="palette__list" id="paletteList" role="listbox"></ul>
  </div>
</div>
```

```js
commandPalette(document.getElementById('palette'), [
  { label: 'Browse design systems', hint: '1,342', action: () => go('/styles') },
  { label: 'Copy the install command', hint: 'npm', action: () => copy('npm i frontend-library') },
]);
```

Copy the `<style>` block marked `── snippet ──`, the markup above and the
`commandPalette` function. Everything under `// demo loop` only animates the
preview — leave it out of your project.

## Accessibility

- The trigger is a real `<button>` with `aria-haspopup` and `aria-expanded`.
- The results list is a `role="listbox"` and each row a `role="option"` with
  `aria-selected`, so screen readers announce the active row.
- The search field is labelled and points at the list with `aria-controls`.
- Focus returns to the trigger when the palette closes.
- `prefers-reduced-motion` is respected — the panel fades in without moving.

## Credits & licence

Original work for Frontend Library, released under the
[MIT licence](../animations/snippets/LICENSE).

The interaction pattern is inspired by the command palettes in Linear and
Raycast; no code was copied from either.

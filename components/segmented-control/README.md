# Segmented Control

An accessible, iOS/macOS-style segmented control component with a fluid gliding pill indicator, WAI-ARIA tablist semantics, keyboard navigation, and reduced-motion awareness.

## Features

- **WAI-ARIA Compliant**: Implements `role="tablist"`, `role="tab"`, and `role="tabpanel"` semantics.
- **Full Keyboard Navigation**: Supports `ArrowLeft`, `ArrowRight`, `Home`, and `End` keys with automatic focus and activation.
- **Fluid Sliding Indicator**: Hardware-accelerated CSS `transform` glider that dynamically measures and slides to the active tab.
- **Responsive**: Auto-reflows on window resize and handles dynamic label widths.
- **Zero Dependencies**: Pure HTML, CSS custom properties, and modern vanilla JavaScript.

## Usage

Include `index.html` or integrate into your HTML/CSS:

```html
<div class="segmented-control" role="tablist" id="my-tabs">
  <div class="segmented-control__glider" id="glider"></div>
  <button class="segmented-control__item" role="tab" aria-selected="true" aria-controls="panel-1">Tab 1</button>
  <button class="segmented-control__item" role="tab" aria-selected="false" aria-controls="panel-2" tabindex="-1">Tab 2</button>
</div>
```

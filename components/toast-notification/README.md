# Toast Notification

A lightweight, accessible, zero-dependency toast notification system with stacking, auto-dismiss, pause-on-hover, and reduced-motion awareness.

## Features

- **Semantic & Accessible**: Uses `role="status"` and `role="alert"` inside an `aria-live="polite"` viewport.
- **Stackable**: Multiple notifications stack gracefully and auto-dismiss after a configurable timeout.
- **Interactive**: Hovering pauses the auto-dismiss timer; includes an explicit close button.
- **Reduced Motion**: Respects `prefers-reduced-motion` with instantaneous transitions.
- **Zero Dependencies**: Pure HTML, CSS custom properties, and modern vanilla JavaScript.

## Usage

Open `index.html` in any browser or copy the CSS and JavaScript into your application:

```javascript
const toast = createToaster(document.getElementById('toast-container'));

toast({
  type: 'success', // 'success' | 'info' | 'error'
  title: 'Changes saved',
  message: 'Your profile details were updated.',
  duration: 4000
});
```

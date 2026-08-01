# IconButton

`IconButton` is the reusable compact action control for icon-only actions.

## Public API

- Native button props, plus required `aria-label`, `variant` (`primary`, `secondary`, `ghost`), `size` (`sm`, `md`, `lg`), `loading`, and `className`.
- It forwards its ref to the native `<button>`.

## Accessibility

An `aria-label` is required because the child icon is hidden from assistive technology. Loading buttons are disabled and expose `aria-busy`.

## Usage

```tsx
<IconButton aria-label="Close" variant="ghost">×</IconButton>
```

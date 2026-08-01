# Button

`Button` is the reusable labeled action control for JARVIS.

## Public API

- Native button props, plus `variant` (`primary`, `secondary`, `ghost`), `size` (`sm`, `md`, `lg`), `leftIcon`, `rightIcon`, `loading`, `fullWidth`, and `className`.
- It forwards its ref to the native `<button>`.

## Accessibility

Use visible text that communicates the action. Loading buttons are disabled, expose `aria-busy`, and announce a loading label to assistive technology.

## Usage

```tsx
<Button variant="primary">Save changes</Button>
```

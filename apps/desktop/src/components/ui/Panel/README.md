# Panel

`Panel` is a larger semantic section surface for grouping a distinct area of content.

## Public API

- Standard section props, plus `padding` (`none`, `sm`, `md`, `lg`), `children`, and `className`.

## Accessibility

It renders a semantic `<section>`. Supply an accessible name with `aria-label` or `aria-labelledby` when the section needs one.

## Usage

```tsx
<Panel aria-label="Assistant activity">Content</Panel>
```

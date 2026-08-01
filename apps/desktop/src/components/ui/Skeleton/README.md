# Skeleton

`Skeleton` is a static placeholder that reserves content space during loading.

## Public API

- Standard span props, plus `variant` (`text`, `circle`, `rectangle`), `size` (`sm`, `md`, `lg`), and `className`.

## Accessibility

It is hidden from assistive technology. The consuming feature must provide meaningful loading status when needed.

## Usage

```tsx
<Skeleton variant="text" size="md" />
```

## Used By

Expected future consumers: Header status, AI Core loading state, Chat history, and Settings loading views.

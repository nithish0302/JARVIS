# Badge

`Badge` presents a compact, non-interactive category or status label.

## Public API

- Standard span props, plus `tone` (`neutral`, `accent`, `success`, `warning`, `error`), `size` (`sm`, `md`), `children`, and `className`.

## Accessibility

Do not rely on tone alone to communicate meaning; always provide descriptive badge text. Use `StatusIndicator` in Milestone 6B for live status announcements.

## Usage

```tsx
<Badge tone="success">Connected</Badge>
```

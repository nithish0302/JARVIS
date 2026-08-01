# Spinner

`Spinner` is a compact loading-status indicator with a restrained token-driven rotation.

## Public API

- Standard span props, plus `label`, `size` (`sm`, `md`, `lg`), and `className`.

## Accessibility

It exposes a polite status with an accessible loading label while the visual ring remains hidden from assistive technology. Its animation is disabled by the global reduced-motion preference.

## Usage

```tsx
<Spinner label="Loading conversation" />
```

## Used By

Expected future consumers: Header status, AI Core initialization, Chat loading states, and Settings saves.

# StatusIndicator

`StatusIndicator` presents a labeled, color-supported application status.

## Public API

- Standard span props, plus required `label`, `tone` (`accent`, `success`, `warning`, `error`), `live` (`off`, `polite`), and `className`.

## Accessibility

The visible label communicates the status without relying on color. Set `live="polite"` when changes should be announced to assistive technology.

## Usage

```tsx
<StatusIndicator label="Online" tone="success" />
```

## Used By

Expected future consumers: Header, AI Core, Chat, voice state, Settings, and automation status.

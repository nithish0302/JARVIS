# Checkbox

`Checkbox` is the reusable labeled native binary-choice control built on the shared `Field` composition.

## Public API

- Native checkbox props except `type`, plus required `label`, optional `description`, `error`, and `className`.
- It forwards its ref to the native checkbox input.

## Accessibility

It preserves native checkbox keyboard and form behavior. The label, description, and error are programmatically associated with the control.

## Usage

```tsx
<Checkbox label="Enable notifications" />
```

## Used By

Expected future consumers: Settings, automation confirmations, chat preferences, and privacy controls.

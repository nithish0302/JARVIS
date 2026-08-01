# Switch

`Switch` is the reusable labeled binary-setting control built on a native checkbox and the shared `Field` composition.

## Public API

- Native checkbox props except `type`, plus required `label`, optional `description`, `error`, and `className`.
- It forwards its ref to the native checkbox input.

## Accessibility

The native checkbox is exposed as `role="switch"`, preserving keyboard and form behavior while communicating an on/off setting. Labels and supporting messages are associated with the control.

## Usage

```tsx
<Switch label="Voice activation" />
```

## Used By

Expected future consumers: Settings, voice controls, AI Core preferences, and automation settings.

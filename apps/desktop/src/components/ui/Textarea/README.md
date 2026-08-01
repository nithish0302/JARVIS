# Textarea

`Textarea` is the reusable labeled multi-line text control built on the shared `Field` composition.

## Public API

- Native textarea props, plus required `label`, optional `description`, `error`, `resize` (`none`, `vertical`, `both`), and `className`.
- It forwards its ref to the native `<textarea>`.

## Accessibility

The label, description, and error are associated with the native control. Errors set `aria-invalid` and are announced by the shared field structure.

## Usage

```tsx
<Textarea label="Instructions" resize="vertical" />
```

## Used By

Expected future consumers: Chat composer, Settings, automation configuration, and developer diagnostics.

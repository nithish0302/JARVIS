# Select

`Select` is the reusable labeled native option-selection control built on the shared `Field` composition.

## Public API

- Native select props, plus required `label`, optional `description`, `error`, `children`, and `className`.
- It forwards its ref to the native `<select>`.

## Accessibility

It retains native select keyboard behavior. The label, description, and error are associated with the control, and errors set `aria-invalid`.

## Usage

```tsx
<Select label="Provider"><option>Automatic</option></Select>
```

## Used By

Expected future consumers: Settings, AI provider selection, voice configuration, and automation preferences.

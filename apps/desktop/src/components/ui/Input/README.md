# Input

`Input` is the reusable labeled single-line text field built on the shared `Field` composition.

## Public API

- Native input props except native `size`, plus required `label`, optional `description`, `error`, `startAdornment`, `endAdornment`, and `className`.
- It forwards its ref to the native `<input>`.

## Accessibility

The label is associated with the input, descriptions and errors are exposed through `aria-describedby`, and errors set `aria-invalid`.

## Usage

```tsx
<Input label="Workspace name" placeholder="JARVIS" />
```

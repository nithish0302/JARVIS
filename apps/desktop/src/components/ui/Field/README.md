# Field

`Field` supplies the shared accessible label, description, required marker, and error-message structure for form controls.

## Public API

- Standard div props, plus `htmlFor`, `label`, `children`, `description`, `descriptionId`, `error`, `errorId`, `required`, and `className`.
- `useFieldIds` provides stable IDs for composed controls.

## Accessibility

`htmlFor` must match the child control ID. Controls should reference provided description and error IDs with `aria-describedby`; errors are announced with `role="alert"`.

## Usage

```tsx
<Field htmlFor="name" label="Name"><input id="name" /></Field>
```

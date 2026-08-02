# SettingsLayout

`SettingsLayout` provides the structural two-column grid for the settings view.

## Public API

- Requires `sidebar` and `children`.

## Accessibility

Maintains structural order for screen readers (sidebar then content).

## Usage

```tsx
<SettingsLayout sidebar={<Sidebar />}>
  <Content />
</SettingsLayout>
```

## Used By

`SettingsView`

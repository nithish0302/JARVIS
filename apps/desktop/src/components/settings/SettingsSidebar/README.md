# SettingsSidebar

`SettingsSidebar` provides vertical navigation between different settings categories.

## Public API

- Requires `activeSection` and `onSectionSelect`.

## Accessibility

It renders a `<nav>` with an accessible label.

## Usage

```tsx
<SettingsSidebar activeSection="about" onSectionSelect={setSection} />
```

## Used By

`SettingsView`

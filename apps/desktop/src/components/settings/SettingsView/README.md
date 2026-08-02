# SettingsView

`SettingsView` is the root component for the settings page.

## Public API

- Takes optional `onClose`.

## Accessibility

Manages focus and sections based on the selected sidebar item.

## Usage

```tsx
<SettingsView onClose={() => setView("chat")} />
```

## Used By

`App`

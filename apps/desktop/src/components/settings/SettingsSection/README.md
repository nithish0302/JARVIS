# SettingsSection

`SettingsSection` provides a standardized header and layout for distinct areas within the settings view.

## Public API

- Requires `title`, `description`, and `children`.

## Accessibility

It renders a semantic `<section>` element with a header group.

## Usage

```tsx
<SettingsSection title="Appearance" description="Customize JARVIS.">
  <Content />
</SettingsSection>
```

## Used By

Settings view sections (e.g., `AIProviderSection`, `AppearanceSection`).

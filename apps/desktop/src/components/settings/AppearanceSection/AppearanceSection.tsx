import { SettingsSection } from "../SettingsSection/SettingsSection";
import { Switch } from "../../ui/Switch/Switch";

export function AppearanceSection() {
  return (
    <SettingsSection
      description="Customize the look and feel of JARVIS."
      title="Appearance"
    >
      <div className="flex max-w-md flex-col gap-[var(--space-4)]">
        <Switch
          defaultChecked
          description="Additional themes coming soon"
          disabled
          label="Dark Mode"
        />
      </div>
    </SettingsSection>
  );
}

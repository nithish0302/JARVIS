import { SettingsSection } from "../SettingsSection/SettingsSection";
import { Divider } from "../../ui/Divider/Divider";

export function AboutSection() {
  return (
    <SettingsSection description="System information." title="About">
      <div className="flex flex-col gap-[var(--space-4)] text-[length:var(--font-size-body)] text-[var(--color-text-primary)]">
        <div className="flex justify-between">
          <span className="font-medium">App Name</span>
          <span className="text-[var(--color-text-secondary)]">JARVIS</span>
        </div>
        <Divider />
        <div className="flex justify-between">
          <span className="font-medium">Version</span>
          <span className="text-[var(--color-text-secondary)]">0.1.0</span>
        </div>
        <Divider />
        <div className="flex justify-between">
          <span className="font-medium">Description</span>
          <span className="text-[var(--color-text-secondary)]">
            A premium AI desktop operating companion
          </span>
        </div>
        <Divider />
        <div className="flex justify-between">
          <span className="font-medium">Author</span>
          <span className="text-[var(--color-text-secondary)]">Nithish</span>
        </div>
      </div>
    </SettingsSection>
  );
}

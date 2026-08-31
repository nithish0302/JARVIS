import { Button } from "../../ui/Button/Button";

export interface SettingsSidebarProps {
  activeSection: string;
  onSectionSelect: (sectionId: string) => void;
}

export function SettingsSidebar({
  activeSection,
  onSectionSelect,
}: SettingsSidebarProps) {
    const navItems = [
      { id: "ai-provider", label: "AI Provider" },
      { id: "personality", label: "Personality" },
      { id: "appearance", label: "Appearance" },
      { id: "plugins", label: "Plugins" },
      { id: "providers", label: "Providers" },
      { id: "about", label: "About" },
    ];

  return (
    <nav aria-label="Settings sections" className="flex w-48 flex-col gap-[var(--space-2)]">
      {navItems.map((item) => (
        <Button
          key={item.id}
          className={
            activeSection === item.id
              ? "bg-[var(--color-surface)] text-[var(--color-accent)]"
              : "text-[var(--color-text-secondary)]"
          }
          onClick={() => onSectionSelect(item.id)}
          variant="ghost"
        >
          <span className="w-full text-left">{item.label}</span>
        </Button>
      ))}
    </nav>
  );
}

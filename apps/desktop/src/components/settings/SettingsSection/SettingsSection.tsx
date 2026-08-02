import type { ReactNode } from "react";
import { Divider } from "../../ui/Divider/Divider";

export interface SettingsSectionProps {
  title: string;
  description: string;
  children: ReactNode;
}

export function SettingsSection({
  title,
  description,
  children,
}: SettingsSectionProps) {
  return (
    <section className="flex flex-col gap-[var(--space-6)]">
      <header className="flex flex-col gap-[var(--space-1)]">
        <h2 className="text-[length:var(--font-size-page)] font-semibold text-[var(--color-text-primary)]">
          {title}
        </h2>
        <p className="text-[length:var(--font-size-body)] text-[var(--color-text-muted)]">
          {description}
        </p>
      </header>
      <Divider />
      <div className="flex flex-col gap-[var(--space-6)]">{children}</div>
    </section>
  );
}

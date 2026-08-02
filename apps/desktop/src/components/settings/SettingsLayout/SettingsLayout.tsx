import type { ReactNode } from "react";

export interface SettingsLayoutProps {
  sidebar: ReactNode;
  children: ReactNode;
}

export function SettingsLayout({ sidebar, children }: SettingsLayoutProps) {
  return (
    <div className="mx-auto flex w-full max-w-5xl gap-[var(--space-8)] p-[var(--space-8)]">
      <aside className="shrink-0">{sidebar}</aside>
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  );
}

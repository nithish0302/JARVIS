import type { ReactNode } from "react";
import { AppHeader } from "./AppHeader";
import { AppMain } from "./AppMain";
import { OverlayLayer } from "./OverlayLayer";
import { StatusBar } from "./StatusBar";

export interface AppShellProps {
  children?: ReactNode;
  onClose?: () => void;
  onSettingsOpen?: () => void;
}

export function AppShell({ children, onClose, onSettingsOpen }: AppShellProps) {
  return (
    <div className="relative grid h-dvh min-h-0 grid-rows-[auto_minmax(0,1fr)_auto] overflow-hidden bg-[var(--color-background)]">
      <a
        className="sr-only z-[var(--z-toast)] rounded-[var(--radius-sm)] bg-[var(--color-accent)] px-[var(--space-3)] py-[var(--space-2)] text-[var(--color-background)] focus:not-sr-only focus:absolute focus:left-[var(--space-4)] focus:top-[var(--space-4)]"
        href="#app-main"
      >
        Skip to main content
      </a>
      <AppHeader onClose={onClose} onSettingsOpen={onSettingsOpen} />
      <AppMain>{children}</AppMain>
      <StatusBar />
      <OverlayLayer />
    </div>
  );
}

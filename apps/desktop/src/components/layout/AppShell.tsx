import type { ReactNode } from "react";
import { AppHeader } from "./AppHeader";
import { AppMain } from "./AppMain";
import { OverlayLayer } from "./OverlayLayer";
import { StatusBar } from "./StatusBar";
import { useAIStore } from "../../stores/useAIStore";
import { cn } from "../../lib/cn";

export interface AppShellProps {
  children?: ReactNode;
  onClose?: () => void;
  onSettingsOpen?: () => void;
}

export function AppShell({ children, onClose, onSettingsOpen }: AppShellProps) {
  const { status, provider, model, memoryCount } = useAIStore();

  const getStatusLabel = () => {
    switch (status) {
      case "idle":
        return `● Ready · ${provider} · ${model}`;
      case "connecting":
        return "● Connecting...";
      case "streaming":
        return "● Thinking...";
      case "error":
        return "● Error";
      case "offline":
        return "● Offline";
      default:
        return "● Ready";
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "idle":
        return "text-[var(--color-success)]";
      case "connecting":
      case "streaming":
        return "text-[var(--color-accent)]";
      case "error":
      case "offline":
        return "text-[var(--color-error)]";
      default:
        return "text-[var(--color-text-muted)]";
    }
  };

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
      <StatusBar
        leftSlot={
          <span className={cn("text-[length:var(--font-size-caption)]", getStatusColor())}>
            {getStatusLabel()}
          </span>
        }
        rightSlot={
          <span className="text-[length:var(--font-size-caption)] text-[var(--color-text-muted)]">
            {memoryCount} memories · v0.1.0
          </span>
        }
      />
      <OverlayLayer />
    </div>
  );
}

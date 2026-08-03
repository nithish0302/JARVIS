import type { ReactNode } from "react";
import { ArrowLeft, Settings } from "lucide-react";
import { cn } from "../../lib/cn";
import { IconButton } from "../ui/IconButton/IconButton";

export interface AppHeaderProps {
  brand?: ReactNode;
  children?: ReactNode;
  className?: string;
  onClose?: () => void;
  onSettingsOpen?: () => void;
}

export function AppHeader({
  brand,
  children,
  className,
  onClose,
  onSettingsOpen,
}: AppHeaderProps) {
  return (
    <header
      aria-label="Application header"
      className={cn(
        "z-[var(--z-header)] flex min-h-[var(--space-16)] items-center justify-between border-b-[var(--color-border-subtle)] border-solid [border-width:var(--border-width)] bg-[var(--color-background-secondary)] px-[var(--space-4)] py-[var(--space-3)]",
        className,
      )}
    >
      <div className="flex items-center gap-[var(--space-2)]">
        {brand || (
          <span className="font-mono text-[length:var(--font-size-section)] font-semibold tracking-wider text-[var(--color-accent)]">
            JARVIS
          </span>
        )}
      </div>
      <div className="flex items-center gap-[var(--space-2)]">
        {children}
        {onClose ? (
          <IconButton aria-label="Back to chat" onClick={onClose} variant="ghost">
            <ArrowLeft aria-hidden="true" className="size-[var(--font-size-xl)]" />
          </IconButton>
        ) : onSettingsOpen ? (
          <IconButton aria-label="Open settings" onClick={onSettingsOpen} variant="ghost">
            <Settings aria-hidden="true" className="size-[var(--font-size-xl)]" />
          </IconButton>
        ) : null}
      </div>
    </header>
  );
}

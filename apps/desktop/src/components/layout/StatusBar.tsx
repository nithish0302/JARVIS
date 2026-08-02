import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export interface StatusBarProps {
  className?: string;
  leftSlot?: ReactNode;
  rightSlot?: ReactNode;
}

export function StatusBar({ className, leftSlot, rightSlot }: StatusBarProps) {
  return (
    <footer
      aria-label="Application status"
      className={cn(
        "z-[var(--z-header)] flex min-h-[var(--space-8)] items-center justify-between border-t-[var(--color-border-subtle)] border-solid [border-width:var(--border-width)] bg-[var(--color-background-secondary)] px-[var(--space-4)] text-[var(--font-size-sm)] text-[var(--color-text-muted)]",
        className,
      )}
    >
      <div className="flex items-center gap-[var(--space-4)] empty:hidden">
        {leftSlot}
      </div>
      <div className="flex items-center gap-[var(--space-4)] empty:hidden">
        {rightSlot}
      </div>
    </footer>
  );
}

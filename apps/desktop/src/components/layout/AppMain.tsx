import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export interface AppMainProps {
  children?: ReactNode;
  className?: string;
}

export function AppMain({ children, className }: AppMainProps) {
  return (
    <main
      className={cn(
        "min-h-0 overflow-x-hidden overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]",
        className,
      )}
      id="app-main"
      tabIndex={-1}
    >
      {children}
    </main>
  );
}

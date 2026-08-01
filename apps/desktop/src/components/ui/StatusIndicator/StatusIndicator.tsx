import type { ComponentPropsWithoutRef } from "react";
import { cn } from "../../../lib/cn";

type StatusTone = "accent" | "success" | "warning" | "error";

export interface StatusIndicatorProps extends ComponentPropsWithoutRef<"span"> {
  label: string;
  tone?: StatusTone;
  live?: "off" | "polite";
}

const toneClasses: Record<StatusTone, string> = {
  accent: "bg-[var(--color-accent)]",
  success: "bg-[var(--color-success)]",
  warning: "bg-[var(--color-warning)]",
  error: "bg-[var(--color-error)]",
};

export function StatusIndicator({
  className,
  label,
  live = "off",
  tone = "accent",
  ...props
}: StatusIndicatorProps) {
  return (
    <span
      {...props}
      aria-live={live === "polite" ? "polite" : undefined}
      className={cn(
        "inline-flex items-center gap-[var(--space-2)] text-[var(--color-text-primary)]",
        className,
      )}
      role={live === "polite" ? "status" : undefined}
    >
      <span
        aria-hidden="true"
        className={cn("size-[var(--space-2)] rounded-[var(--radius-full)]", toneClasses[tone])}
      />
      {label}
    </span>
  );
}

import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { cn } from "../../../lib/cn";

type BadgeTone = "neutral" | "accent" | "success" | "warning" | "error";
type BadgeSize = "sm" | "md";

export interface BadgeProps extends ComponentPropsWithoutRef<"span"> {
  children: ReactNode;
  tone?: BadgeTone;
  size?: BadgeSize;
}

const toneClasses: Record<BadgeTone, string> = {
  neutral: "border-[var(--color-border)] text-[var(--color-text-secondary)]",
  accent: "border-[var(--color-accent)] text-[var(--color-accent)]",
  success: "border-[var(--color-success)] text-[var(--color-success)]",
  warning: "border-[var(--color-warning)] text-[var(--color-warning)]",
  error: "border-[var(--color-error)] text-[var(--color-error)]",
};

const sizeClasses: Record<BadgeSize, string> = {
  sm: "px-[var(--space-2)] py-[var(--space-1)] text-[length:var(--font-size-caption)] leading-[var(--line-height-caption)]",
  md: "px-[var(--space-3)] py-[var(--space-1)] text-[length:var(--font-size-sm)] leading-[var(--line-height-sm)]",
};

export function Badge({ children, className, size = "sm", tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      {...props}
      className={cn(
        "inline-flex items-center rounded-[var(--radius-full)] border-solid [border-width:var(--border-width)] bg-[var(--color-surface)] font-[var(--font-weight-medium)]",
        toneClasses[tone],
        sizeClasses[size],
        className,
      )}
    >
      {children}
    </span>
  );
}

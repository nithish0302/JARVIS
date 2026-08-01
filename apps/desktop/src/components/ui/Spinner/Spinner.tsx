import type { ComponentPropsWithoutRef } from "react";
import { cn } from "../../../lib/cn";

type SpinnerSize = "sm" | "md" | "lg";

export interface SpinnerProps extends ComponentPropsWithoutRef<"span"> {
  label?: string;
  size?: SpinnerSize;
}

const sizeClasses: Record<SpinnerSize, string> = {
  sm: "size-[var(--icon-size-sm)]",
  md: "size-[var(--icon-size-md)]",
  lg: "size-[var(--icon-size-lg)]",
};

export function Spinner({ className, label = "Loading", size = "md", ...props }: SpinnerProps) {
  return (
    <span
      {...props}
      aria-label={label}
      aria-live="polite"
      className={cn("inline-flex", className)}
      role="status"
    >
      <span
        aria-hidden="true"
        className={cn(
          "jarvis-spinner rounded-[var(--radius-full)] border-solid [border-width:var(--border-width)] border-[var(--color-border-subtle)] border-t-[var(--color-accent)]",
          sizeClasses[size],
        )}
      />
      <span className="sr-only">{label}</span>
    </span>
  );
}

import type { ComponentPropsWithoutRef } from "react";
import { cn } from "../../../lib/cn";

export interface DividerProps extends ComponentPropsWithoutRef<"hr"> {
  orientation?: "horizontal" | "vertical";
}

export function Divider({ className, orientation = "horizontal", ...props }: DividerProps) {
  if (orientation === "vertical") {
    return (
      <div
        {...props}
        aria-orientation="vertical"
        className={cn("h-full w-[var(--border-width)] bg-[var(--color-border-subtle)]", className)}
        role="separator"
      />
    );
  }

  return (
    <hr
      {...props}
      className={cn("h-[var(--border-width)] w-full border-0 bg-[var(--color-border-subtle)]", className)}
    />
  );
}

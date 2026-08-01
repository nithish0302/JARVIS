import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { cn } from "../../../lib/cn";
import { surfaceBaseClasses, surfacePaddingClasses, type SurfacePadding } from "../shared/surfaceStyles";

export interface PanelProps extends ComponentPropsWithoutRef<"section"> {
  children: ReactNode;
  padding?: SurfacePadding;
}

export function Panel({ children, className, padding = "lg", ...props }: PanelProps) {
  return (
    <section
      {...props}
      className={cn(
        surfaceBaseClasses,
        "rounded-[var(--radius-lg)] bg-[var(--color-surface)]",
        surfacePaddingClasses[padding],
        className,
      )}
    >
      {children}
    </section>
  );
}

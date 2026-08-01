import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { cn } from "../../../lib/cn";
import { surfaceBaseClasses, surfacePaddingClasses, type SurfacePadding } from "../shared/surfaceStyles";

type CardVariant = "card" | "panel";

export interface CardProps extends ComponentPropsWithoutRef<"div"> {
  children: ReactNode;
  variant?: CardVariant;
  padding?: SurfacePadding;
}

const variantClasses: Record<CardVariant, string> = {
  card: "rounded-[var(--radius-md)]",
  panel: "rounded-[var(--radius-lg)]",
};

export function Card({ children, className, padding = "md", variant = "card", ...props }: CardProps) {
  return (
    <div
      {...props}
      className={cn(
        surfaceBaseClasses,
        variantClasses[variant],
        surfacePaddingClasses[padding],
        className,
      )}
    >
      {children}
    </div>
  );
}

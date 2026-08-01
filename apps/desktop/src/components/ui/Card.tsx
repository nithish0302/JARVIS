import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { cn } from "../../lib/cn";

type CardVariant = "card" | "panel";
type CardPadding = "none" | "sm" | "md" | "lg";

export interface CardProps extends ComponentPropsWithoutRef<"div"> {
  children: ReactNode;
  variant?: CardVariant;
  padding?: CardPadding;
}

const variantClasses: Record<CardVariant, string> = {
  card: "rounded-[var(--radius-md)]",
  panel: "rounded-[var(--radius-lg)]",
};

const paddingClasses: Record<CardPadding, string> = {
  none: "",
  sm: "p-[var(--space-3)]",
  md: "p-[var(--space-4)]",
  lg: "p-[var(--space-6)]",
};

export function Card({ children, className, padding = "md", variant = "card", ...props }: CardProps) {
  return (
    <div
      {...props}
      className={cn(
        "border-solid [border-width:var(--border-width)] border-[var(--color-border-subtle)] bg-[var(--color-background-secondary)] text-[var(--color-text-primary)] shadow-[var(--shadow-sm)]",
        variantClasses[variant],
        paddingClasses[padding],
        className,
      )}
    >
      {children}
    </div>
  );
}

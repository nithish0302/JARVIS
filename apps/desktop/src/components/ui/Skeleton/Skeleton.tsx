import type { ComponentPropsWithoutRef } from "react";
import { cn } from "../../../lib/cn";

type SkeletonVariant = "text" | "circle" | "rectangle";
type SkeletonSize = "sm" | "md" | "lg";

export interface SkeletonProps extends ComponentPropsWithoutRef<"span"> {
  variant?: SkeletonVariant;
  size?: SkeletonSize;
}

const variantClasses: Record<SkeletonVariant, string> = {
  text: "w-[var(--space-16)] rounded-[var(--radius-sm)]",
  circle: "rounded-[var(--radius-full)]",
  rectangle: "w-[var(--space-16)] rounded-[var(--radius-sm)]",
};

const sizeClasses: Record<SkeletonSize, string> = {
  sm: "h-[var(--space-4)]",
  md: "h-[var(--space-6)]",
  lg: "h-[var(--space-8)]",
};

const circleSizeClasses: Record<SkeletonSize, string> = {
  sm: "size-[var(--space-4)]",
  md: "size-[var(--space-6)]",
  lg: "size-[var(--space-8)]",
};

export function Skeleton({ className, size = "md", variant = "text", ...props }: SkeletonProps) {
  return (
    <span
      {...props}
      aria-hidden="true"
      className={cn(
        "inline-block bg-[var(--color-surface-raised)] [opacity:var(--opacity-hover)]",
        variantClasses[variant],
        variant === "circle" ? circleSizeClasses[size] : sizeClasses[size],
        className,
      )}
    />
  );
}

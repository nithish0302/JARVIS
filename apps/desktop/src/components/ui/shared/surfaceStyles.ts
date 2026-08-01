export type SurfacePadding = "none" | "sm" | "md" | "lg";

export const surfaceBaseClasses =
  "border-solid [border-width:var(--border-width)] border-[var(--color-border-subtle)] bg-[var(--color-background-secondary)] text-[var(--color-text-primary)] shadow-[var(--shadow-sm)]";

export const surfacePaddingClasses: Record<SurfacePadding, string> = {
  none: "",
  sm: "p-[var(--space-3)]",
  md: "p-[var(--space-4)]",
  lg: "p-[var(--space-6)]",
};

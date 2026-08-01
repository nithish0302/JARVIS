export type ButtonVariant = "primary" | "secondary" | "ghost";
export type ButtonSize = "sm" | "md" | "lg";

export const buttonBaseClasses =
  "inline-flex items-center justify-center gap-[var(--space-2)] rounded-[var(--radius-sm)] border-solid [border-width:var(--border-width)] transition-[background-color,border-color,color,box-shadow,transform] duration-[var(--duration-fast)] ease-[var(--ease-standard)] hover:shadow-[var(--shadow-sm)] active:[transform:scale(var(--scale-active))] focus-visible:outline-none disabled:cursor-not-allowed disabled:[opacity:var(--opacity-disabled)] disabled:border-[var(--color-border-subtle)] disabled:bg-[var(--color-background-secondary)] disabled:text-[var(--color-text-secondary)]";

export const buttonVariantClasses: Record<ButtonVariant, string> = {
  primary:
    "border-[var(--color-accent)] bg-[var(--color-accent)] text-[var(--color-background)] hover:bg-[var(--color-accent-hover)]",
  secondary:
    "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-primary)] hover:border-[var(--color-accent-hover)]",
  ghost:
    "border-transparent bg-transparent text-[var(--color-text-primary)] hover:bg-[var(--color-background-secondary)]",
};

export const buttonSizeClasses: Record<ButtonSize, string> = {
  sm: "min-h-[var(--space-8)] px-[var(--space-3)] py-[var(--space-1)]",
  md: "min-h-[var(--space-12)] px-[var(--space-4)] py-[var(--space-2)]",
  lg: "min-h-[var(--space-16)] px-[var(--space-6)] py-[var(--space-3)]",
};

export const iconButtonSizeClasses: Record<ButtonSize, string> = {
  sm: "size-[var(--space-8)]",
  md: "size-[var(--space-12)]",
  lg: "size-[var(--space-16)]",
};

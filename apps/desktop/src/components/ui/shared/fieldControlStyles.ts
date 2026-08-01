export const fieldControlBaseClasses =
  "w-full rounded-[var(--radius-sm)] border-solid [border-width:var(--border-width)] bg-[var(--color-surface)] px-[var(--space-3)] py-[var(--space-2)] text-[length:var(--font-size-body)] leading-[var(--line-height-body)] text-[var(--color-text-primary)] transition-[border-color,box-shadow] duration-[var(--duration-fast)] ease-[var(--ease-standard)] focus:border-[var(--color-border-focus)] placeholder:text-[var(--color-text-secondary)]";

export const fieldControlContainerClasses =
  "flex items-center gap-[var(--space-2)] rounded-[var(--radius-sm)] border-solid [border-width:var(--border-width)] bg-[var(--color-surface)] px-[var(--space-3)] py-[var(--space-2)] transition-[border-color,box-shadow] duration-[var(--duration-fast)] ease-[var(--ease-standard)] focus-within:border-[var(--color-border-focus)]";

export const fieldControlBorderClasses = {
  default: "border-[var(--color-border)]",
  error: "border-[var(--color-error)]",
};

export const fieldControlTextClasses =
  "min-w-0 flex-1 bg-transparent text-[length:var(--font-size-body)] leading-[var(--line-height-body)] text-[var(--color-text-primary)] outline-none placeholder:text-[var(--color-text-secondary)]";

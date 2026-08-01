import { forwardRef, useId, type ComponentPropsWithoutRef, type ComponentRef, type ReactNode } from "react";
import { cn } from "../../lib/cn";

export interface InputProps extends Omit<ComponentPropsWithoutRef<"input">, "size"> {
  label: string;
  description?: string;
  error?: string;
  startAdornment?: ReactNode;
  endAdornment?: ReactNode;
}

export const Input = forwardRef<ComponentRef<"input">, InputProps>(function Input(
  {
    "aria-describedby": ariaDescribedBy,
    className,
    description,
    endAdornment,
    error,
    id,
    label,
    startAdornment,
    ...props
  },
  ref,
) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const descriptionId = description ? `${inputId}-description` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;

  return (
    <div className="flex w-full flex-col gap-[var(--space-2)]">
      <label className="text-[var(--color-text-primary)]" htmlFor={inputId}>
        {label}
      </label>
      <div
        className={cn(
          "flex items-center gap-[var(--space-2)] rounded-[var(--radius-sm)] border-solid [border-width:var(--border-width)] bg-[var(--color-surface)] px-[var(--space-3)] py-[var(--space-2)] transition-[border-color,box-shadow] duration-[var(--duration-fast)] focus-within:border-[var(--color-accent)]",
          error ? "border-[var(--color-error)]" : "border-[var(--color-border)]",
        )}
      >
        {startAdornment ? <span aria-hidden="true">{startAdornment}</span> : null}
        <input
          {...props}
          ref={ref}
          aria-describedby={cn(ariaDescribedBy, descriptionId, errorId) || undefined}
          aria-invalid={error ? true : props["aria-invalid"]}
          className={cn(
            "min-w-0 flex-1 bg-transparent text-[var(--color-text-primary)] outline-none placeholder:text-[var(--color-text-secondary)]",
            className,
          )}
          id={inputId}
        />
        {endAdornment ? <span aria-hidden="true">{endAdornment}</span> : null}
      </div>
      {description ? (
        <p className="text-[var(--color-text-secondary)]" id={descriptionId}>
          {description}
        </p>
      ) : null}
      {error ? (
        <p className="text-[var(--color-error)]" id={errorId}>
          {error}
        </p>
      ) : null}
    </div>
  );
});

import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { cn } from "../../../lib/cn";

export interface FieldProps extends ComponentPropsWithoutRef<"div"> {
  children: ReactNode;
  description?: ReactNode;
  descriptionId?: string;
  error?: ReactNode;
  errorId?: string;
  htmlFor: string;
  label: ReactNode;
  required?: boolean;
}

export function Field({
  children,
  className,
  description,
  descriptionId,
  error,
  errorId,
  htmlFor,
  label,
  required = false,
  ...props
}: FieldProps) {
  return (
    <div {...props} className={cn("flex w-full flex-col gap-[var(--space-2)]", className)}>
      <label
        className="font-[var(--font-weight-medium)] text-[length:var(--font-size-sm)] leading-[var(--line-height-sm)] text-[var(--color-text-primary)]"
        htmlFor={htmlFor}
      >
        {label}
        {required ? (
          <span aria-hidden="true" className="ml-[var(--space-1)] text-[var(--color-error)]">
            *
          </span>
        ) : null}
      </label>
      {children}
      {description ? (
        <p
          className="text-[length:var(--font-size-sm)] leading-[var(--line-height-sm)] text-[var(--color-text-secondary)]"
          id={descriptionId}
        >
          {description}
        </p>
      ) : null}
      {error ? (
        <p
          className="text-[length:var(--font-size-sm)] leading-[var(--line-height-sm)] text-[var(--color-error)]"
          id={errorId}
          role="alert"
        >
          {error}
        </p>
      ) : null}
    </div>
  );
}

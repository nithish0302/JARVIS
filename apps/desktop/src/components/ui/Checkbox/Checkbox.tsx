import { forwardRef, type ComponentPropsWithoutRef, type ComponentRef } from "react";
import { cn } from "../../../lib/cn";
import { Field } from "../Field/Field";
import { useFieldIds } from "../Field/useFieldIds";

export interface CheckboxProps extends Omit<ComponentPropsWithoutRef<"input">, "type"> {
  label: string;
  description?: string;
  error?: string;
}

export const Checkbox = forwardRef<ComponentRef<"input">, CheckboxProps>(function Checkbox(
  { "aria-describedby": ariaDescribedBy, className, description, error, id, label, required, ...props },
  ref,
) {
  const { controlId, descriptionId, errorId } = useFieldIds({ description, error, id });

  return (
    <Field
      description={description}
      descriptionId={descriptionId}
      error={error}
      errorId={errorId}
      htmlFor={controlId}
      label={label}
      required={required}
    >
      <input
        {...props}
        ref={ref}
        aria-describedby={cn(ariaDescribedBy, descriptionId, errorId) || undefined}
        aria-invalid={error ? true : props["aria-invalid"]}
        className={cn(
          "size-[var(--space-4)] rounded-[var(--radius-sm)] border-[var(--color-border)] bg-[var(--color-surface)] accent-[var(--color-accent)]",
          className,
        )}
        id={controlId}
        required={required}
        type="checkbox"
      />
    </Field>
  );
});

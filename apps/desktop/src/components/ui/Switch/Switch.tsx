import { forwardRef, type ComponentPropsWithoutRef, type ComponentRef } from "react";
import { cn } from "../../../lib/cn";
import { Field } from "../Field/Field";
import { useFieldIds } from "../Field/useFieldIds";

export interface SwitchProps extends Omit<ComponentPropsWithoutRef<"input">, "type"> {
  label: string;
  description?: string;
  error?: string;
}

export const Switch = forwardRef<ComponentRef<"input">, SwitchProps>(function Switch(
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
          "relative h-[var(--space-6)] w-[var(--space-12)] appearance-none rounded-[var(--radius-full)] border-solid [border-width:var(--border-width)] border-[var(--color-border)] bg-[var(--color-surface)] transition-[background-color,border-color] duration-[var(--duration-fast)] ease-[var(--ease-standard)] before:absolute before:left-[var(--space-1)] before:top-[var(--space-1)] before:size-[var(--space-4)] before:rounded-[var(--radius-full)] before:bg-[var(--color-text-primary)] before:transition-transform before:duration-[var(--duration-fast)] before:ease-[var(--ease-standard)] checked:border-[var(--color-accent)] checked:bg-[var(--color-accent)] checked:before:[transform:translateX(var(--space-6))] disabled:cursor-not-allowed disabled:[opacity:var(--opacity-disabled)]",
          className,
        )}
        id={controlId}
        required={required}
        role="switch"
        type="checkbox"
      />
    </Field>
  );
});

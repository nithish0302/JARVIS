import { forwardRef, type ComponentPropsWithoutRef, type ComponentRef, type ReactNode } from "react";
import { cn } from "../../../lib/cn";
import { Field } from "../Field/Field";
import { useFieldIds } from "../Field/useFieldIds";
import { fieldControlBaseClasses, fieldControlBorderClasses } from "../shared/fieldControlStyles";

export interface SelectProps extends ComponentPropsWithoutRef<"select"> {
  children: ReactNode;
  label: string;
  description?: string;
  error?: string;
}

export const Select = forwardRef<ComponentRef<"select">, SelectProps>(function Select(
  { "aria-describedby": ariaDescribedBy, children, className, description, error, id, label, required, ...props },
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
      <select
        {...props}
        ref={ref}
        aria-describedby={cn(ariaDescribedBy, descriptionId, errorId) || undefined}
        aria-invalid={error ? true : props["aria-invalid"]}
        className={cn(
          fieldControlBaseClasses,
          "pr-[var(--space-8)]",
          error ? fieldControlBorderClasses.error : fieldControlBorderClasses.default,
          className,
        )}
        id={controlId}
        required={required}
      >
        {children}
      </select>
    </Field>
  );
});

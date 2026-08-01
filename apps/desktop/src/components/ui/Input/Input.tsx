import { forwardRef, type ComponentPropsWithoutRef, type ComponentRef, type ReactNode } from "react";
import { cn } from "../../../lib/cn";
import { Field } from "../Field/Field";
import { useFieldIds } from "../Field/useFieldIds";
import {
  fieldControlBorderClasses,
  fieldControlContainerClasses,
  fieldControlTextClasses,
} from "../shared/fieldControlStyles";

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
    required,
    startAdornment,
    ...props
  },
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
      <div
        className={cn(
          fieldControlContainerClasses,
          error ? fieldControlBorderClasses.error : fieldControlBorderClasses.default,
        )}
      >
        {startAdornment ? <span aria-hidden="true">{startAdornment}</span> : null}
        <input
          {...props}
          ref={ref}
          aria-describedby={cn(ariaDescribedBy, descriptionId, errorId) || undefined}
          aria-invalid={error ? true : props["aria-invalid"]}
          className={cn(fieldControlTextClasses, className)}
          id={controlId}
          required={required}
        />
        {endAdornment ? <span aria-hidden="true">{endAdornment}</span> : null}
      </div>
    </Field>
  );
});

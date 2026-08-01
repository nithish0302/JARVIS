import { forwardRef, type ComponentPropsWithoutRef, type ComponentRef } from "react";
import { cn } from "../../../lib/cn";
import { Field } from "../Field/Field";
import { useFieldIds } from "../Field/useFieldIds";
import { fieldControlBaseClasses, fieldControlBorderClasses } from "../shared/fieldControlStyles";

type TextareaResize = "none" | "vertical" | "both";

export interface TextareaProps extends ComponentPropsWithoutRef<"textarea"> {
  label: string;
  description?: string;
  error?: string;
  resize?: TextareaResize;
}

const resizeClasses: Record<TextareaResize, string> = {
  none: "resize-none",
  vertical: "resize-y",
  both: "resize",
};

export const Textarea = forwardRef<ComponentRef<"textarea">, TextareaProps>(function Textarea(
  { "aria-describedby": ariaDescribedBy, className, description, error, id, label, required, resize = "vertical", ...props },
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
      <textarea
        {...props}
        ref={ref}
        aria-describedby={cn(ariaDescribedBy, descriptionId, errorId) || undefined}
        aria-invalid={error ? true : props["aria-invalid"]}
        className={cn(
          fieldControlBaseClasses,
          error ? fieldControlBorderClasses.error : fieldControlBorderClasses.default,
          resizeClasses[resize],
          className,
        )}
        id={controlId}
        required={required}
      />
    </Field>
  );
});

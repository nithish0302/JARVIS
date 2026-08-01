import { forwardRef, type ComponentPropsWithoutRef, type ComponentRef, type ReactNode } from "react";
import { cn } from "../../../lib/cn";
import {
  buttonBaseClasses,
  buttonVariantClasses,
  iconButtonSizeClasses,
  type ButtonSize,
  type ButtonVariant,
} from "../shared/buttonStyles";

export interface IconButtonProps
  extends Omit<ComponentPropsWithoutRef<"button">, "aria-label"> {
  "aria-label": string;
  children: ReactNode;
  loading?: boolean;
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export const IconButton = forwardRef<ComponentRef<"button">, IconButtonProps>(function IconButton(
  {
    "aria-label": ariaLabel,
    children,
    className,
    disabled,
    loading = false,
    size = "md",
    type = "button",
    variant = "primary",
    ...props
  },
  ref,
) {
  return (
    <button
      {...props}
      ref={ref}
      aria-busy={loading || undefined}
      aria-label={ariaLabel}
      className={cn(
        buttonBaseClasses,
        buttonVariantClasses[variant],
        iconButtonSizeClasses[size],
        className,
      )}
      disabled={disabled || loading}
      type={type}
    >
      <span aria-hidden="true">{children}</span>
      {loading ? <span className="sr-only">Loading</span> : null}
    </button>
  );
});

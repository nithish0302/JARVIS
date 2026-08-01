import { forwardRef, type ComponentPropsWithoutRef, type ComponentRef, type ReactNode } from "react";
import { cn } from "../../../lib/cn";
import {
  buttonBaseClasses,
  buttonSizeClasses,
  buttonVariantClasses,
  type ButtonSize,
  type ButtonVariant,
} from "../shared/buttonStyles";

export interface ButtonProps extends ComponentPropsWithoutRef<"button"> {
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  loading?: boolean;
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
}

export const Button = forwardRef<ComponentRef<"button">, ButtonProps>(function Button(
  {
    children,
    className,
    disabled,
    fullWidth = false,
    leftIcon,
    loading = false,
    rightIcon,
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
      className={cn(
        buttonBaseClasses,
        buttonVariantClasses[variant],
        buttonSizeClasses[size],
        fullWidth && "w-full",
        className,
      )}
      disabled={disabled || loading}
      type={type}
    >
      {leftIcon ? <span aria-hidden="true">{leftIcon}</span> : null}
      <span>{children}</span>
      {loading ? <span aria-hidden="true">…</span> : null}
      {rightIcon ? <span aria-hidden="true">{rightIcon}</span> : null}
      {loading ? <span className="sr-only">Loading</span> : null}
    </button>
  );
});

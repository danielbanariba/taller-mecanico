import type { ButtonHTMLAttributes, ReactNode } from "react";

import { Spinner } from "./Spinner";
import { BUTTON_VARIANT_CLASSES, type ButtonVariant } from "./buttonVariants";

export type { ButtonVariant };

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  /** Shows a spinner and disables the button; use for in-flight submits. */
  loading?: boolean;
  children: ReactNode;
}

/**
 * Atomic, presentational button sized for a greasy-handed tap on a cheap
 * Android screen: a 48px-tall target is the Material Design minimum, not
 * decoration.
 */
export function Button({
  variant = "primary",
  loading = false,
  disabled,
  className = "",
  children,
  ...rest
}: ButtonProps) {
  const isDisabled = disabled ?? loading;
  return (
    <button
      type="button"
      {...rest}
      disabled={isDisabled}
      aria-busy={loading}
      className={`inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl px-4 text-lg font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${BUTTON_VARIANT_CLASSES[variant]} ${className}`}
    >
      {loading ? <Spinner /> : null}
      {children}
    </button>
  );
}

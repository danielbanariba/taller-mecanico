import type { ButtonHTMLAttributes, ReactNode } from "react";

import { Spinner } from "./Spinner";
import { BUTTON_VARIANT_CLASSES, type ButtonVariant } from "./buttonVariants";

export type { ButtonVariant };

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  /** Shows a spinner and disables the button; use for in-flight submits. */
  loading?: boolean;
  /**
   * Whether the button stretches to fill its container. Defaults to `true`
   * for the common full-bleed mobile layout; set to `false` for a button
   * that should size to its label plus padding instead (e.g. a header
   * trigger). Never combine this with a `w-auto`/`w-*` class in `className`
   * -- Tailwind has no class-merging, so two conflicting width utilities
   * leave the outcome to generated-CSS source order, not JSX order.
   */
  fullWidth?: boolean;
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
  fullWidth = true,
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
      className={`inline-flex min-h-12 items-center justify-center gap-2 rounded-xl px-4 text-lg font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${fullWidth ? "w-full" : ""} ${BUTTON_VARIANT_CLASSES[variant]} ${className}`}
    >
      {loading ? <Spinner /> : null}
      {children}
    </button>
  );
}

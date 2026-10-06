import type { ButtonHTMLAttributes, ReactNode } from "react";

import { Spinner } from "./Spinner";

export type ButtonVariant = "primary" | "secondary" | "destructive";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  /** Shows a spinner and disables the button; use for in-flight submits. */
  loading?: boolean;
  children: ReactNode;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-brand-primary text-brand-on-primary active:bg-brand-secondary",
  secondary:
    "bg-brand-card text-brand-primary border border-brand-border active:bg-brand-muted",
  destructive: "bg-brand-destructive text-brand-on-destructive active:bg-red-700",
};

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
      className={`inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl px-4 text-lg font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${VARIANT_CLASSES[variant]} ${className}`}
    >
      {loading ? <Spinner /> : null}
      {children}
    </button>
  );
}

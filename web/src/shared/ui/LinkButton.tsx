import type { ReactNode } from "react";
import { Link, type LinkProps } from "react-router";

import { BUTTON_VARIANT_CLASSES, type ButtonVariant } from "./buttonVariants";

export interface LinkButtonProps extends Omit<LinkProps, "className" | "children"> {
  variant?: ButtonVariant;
  className?: string;
  children: ReactNode;
}

/**
 * Atomic, presentational navigation link styled like `Button`. Renders a
 * single `<a>` (react-router's `Link`) -- never a `<button>` nested inside
 * one, which is invalid HTML and gives assistive tech and keyboard users
 * two overlapping interactive elements with the same accessible name.
 * Use this instead of wrapping a `Button` in a `Link` for any action that
 * navigates rather than submitting or mutating something in place.
 */
export function LinkButton({ variant = "primary", className = "", children, ...rest }: LinkButtonProps) {
  return (
    <Link
      {...rest}
      className={`inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl px-4 text-lg font-semibold transition-colors ${BUTTON_VARIANT_CLASSES[variant]} ${className}`}
    >
      {children}
    </Link>
  );
}

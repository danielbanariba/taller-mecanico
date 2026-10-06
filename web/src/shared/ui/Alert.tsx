import type { ReactNode } from "react";

export type AlertVariant = "error" | "info";

export interface AlertProps {
  variant?: AlertVariant;
  children: ReactNode;
}

const VARIANT_CLASSES: Record<AlertVariant, string> = {
  error: "bg-red-50 text-brand-destructive border-brand-destructive",
  info: "bg-sky-50 text-brand-accent border-brand-accent",
};

/**
 * Atomic inline banner for request-level feedback (API errors, confirmations).
 * Uses `role="alert"` so screen readers announce it without the color being
 * the only signal.
 */
export function Alert({ variant = "error", children }: AlertProps) {
  return (
    <div
      role="alert"
      className={`rounded-xl border px-4 py-3 text-base font-medium ${VARIANT_CLASSES[variant]}`}
    >
      {children}
    </div>
  );
}

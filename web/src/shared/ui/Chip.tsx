import type { ButtonHTMLAttributes } from "react";

export interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active: boolean;
}

/** Atomic toggle chip, used for the inventory list's filter row. */
export function Chip({ active, className = "", children, ...rest }: ChipProps) {
  return (
    <button
      type="button"
      aria-pressed={active}
      className={`min-h-12 rounded-full border px-4 text-base font-semibold transition-colors ${
        active
          ? "border-brand-primary bg-brand-primary text-brand-on-primary"
          : "border-brand-border bg-brand-card text-brand-primary"
      } ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

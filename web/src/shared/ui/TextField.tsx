import type { InputHTMLAttributes } from "react";
import { useId } from "react";

export interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  /** Shown below the input in the destructive color; also read by screen readers. */
  error?: string;
  /** Persistent helper text shown when there is no error. */
  helperText?: string;
}

/**
 * Atomic, presentational text input with a visible label (never
 * placeholder-only) and a 48px-tall field, legible for a mechanic reading
 * their phone in bright daylight.
 */
export function TextField({
  label,
  error,
  helperText,
  id,
  className = "",
  ...rest
}: TextFieldProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const helperId = `${inputId}-helper`;
  const errorId = `${inputId}-error`;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-base font-medium text-brand-foreground">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : helperText ? helperId : undefined}
        className={`min-h-12 rounded-xl border px-4 text-base text-brand-foreground outline-none focus:ring-2 focus:ring-brand-accent ${
          error ? "border-brand-destructive" : "border-brand-border"
        } ${className}`}
        {...rest}
      />
      {error ? (
        <p id={errorId} role="alert" className="text-sm font-medium text-brand-destructive">
          {error}
        </p>
      ) : helperText ? (
        <p id={helperId} className="text-sm text-brand-muted-foreground">
          {helperText}
        </p>
      ) : null}
    </div>
  );
}

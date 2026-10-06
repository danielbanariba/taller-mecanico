import type { TextareaHTMLAttributes } from "react";
import { useId } from "react";

export interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  /** Shown below the field in the destructive color; also read by screen readers. */
  error?: string;
  /** Persistent helper text shown when there is no error. */
  helperText?: string;
}

/**
 * Atomic, presentational multi-line text field with a visible label, sized
 * for free-text notes on a phone screen.
 */
export function TextArea({ label, error, helperText, id, className = "", rows = 3, ...rest }: TextAreaProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const helperId = `${fieldId}-helper`;
  const errorId = `${fieldId}-error`;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={fieldId} className="text-base font-medium text-brand-foreground">
        {label}
      </label>
      <textarea
        id={fieldId}
        rows={rows}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : helperText ? helperId : undefined}
        className={`rounded-xl border px-4 py-3 text-base text-brand-foreground outline-none focus:ring-2 focus:ring-brand-accent ${
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

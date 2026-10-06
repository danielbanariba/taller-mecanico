import type { ReactNode } from "react";

export interface DialogProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

/**
 * Atomic modal dialog for a focused, one-decision interaction (a physical
 * count, a confirmation). Closes on backdrop tap, which doubles as the
 * escape route required for a confirmation dialog.
 */
export function Dialog({ open, title, onClose, children }: DialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="w-full max-w-sm rounded-2xl bg-brand-card p-6 shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="mb-4 text-xl font-bold text-brand-primary">{title}</h2>
        {children}
      </div>
    </div>
  );
}

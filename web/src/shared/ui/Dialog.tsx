import { useEffect, useRef, type ReactNode } from "react";

export interface DialogProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

function focusableIn(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR));
}

/**
 * Atomic modal dialog for a focused, one-decision interaction (a physical
 * count, a confirmation). Behaves as `aria-modal` promises: on open, focus
 * moves to its first control; Tab and Shift+Tab cycle inside it; Escape and
 * a backdrop tap close it; on close, focus returns to whatever opened it.
 *
 * A small effect instead of the native `<dialog>` element, whose
 * `showModal()` the test environment (jsdom) does not implement. The dialog
 * moves focus itself, so its children must not use `autoFocus`: React
 * applies that before this effect runs, and the opener to return focus to
 * would already be lost.
 */
export function Dialog({ open, title, onClose, children }: DialogProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  });

  useEffect(() => {
    const panel = panelRef.current;
    if (!open || !panel) {
      return;
    }

    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    (focusableIn(panel)[0] ?? panel).focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onCloseRef.current();
        return;
      }
      if (event.key !== "Tab" || !panel) {
        return;
      }
      const focusable = focusableIn(panel);
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (!first || !last) {
        event.preventDefault();
        panel.focus();
        return;
      }
      const active = document.activeElement;
      const outside = !panel.contains(active);
      if (event.shiftKey && (active === first || outside)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (active === last || outside)) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      opener?.focus();
    };
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 sm:items-center sm:px-4"
      onClick={onClose}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        // Below `sm`, anchored to the bottom as a full-width sheet: rounded
        // only on top, capped height with its own scroll for long content,
        // and bottom padding that grows to clear a phone's home-indicator
        // safe area. From `sm` up, the original centered card is unchanged.
        className="max-h-[85vh] w-full overflow-y-auto rounded-t-2xl bg-brand-card p-6 pb-[max(1.5rem,env(safe-area-inset-bottom))] shadow-xl outline-none sm:max-h-none sm:max-w-sm sm:overflow-visible sm:rounded-2xl sm:pb-6"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="mb-4 text-xl font-bold text-brand-primary">{title}</h2>
        {children}
      </div>
    </div>
  );
}

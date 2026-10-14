export interface NavIconProps {
  className?: string;
}

/**
 * Clipboard glyph for the Órdenes tab. Purely decorative: the tab's
 * accessible name comes from its label text, never from this icon, so it
 * is always `aria-hidden` and never receives a programmatic name of its
 * own (no `<title>`, no `role="img"`).
 */
export function WorkOrdersIcon({ className }: NavIconProps) {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <rect x="6" y="4" width="12" height="17" rx="2" />
      <path d="M9 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1" />
      <path d="M9 10.5h6M9 14h6M9 17.5h3" />
    </svg>
  );
}

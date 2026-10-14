export interface NavIconProps {
  className?: string;
}

/**
 * Person glyph for the Clientes tab. Purely decorative: the tab's
 * accessible name comes from its label text, never from this icon, so it
 * is always `aria-hidden` and never receives a programmatic name of its
 * own (no `<title>`, no `role="img"`).
 */
export function CustomersIcon({ className }: NavIconProps) {
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
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 20c0-3.6 3.13-6 7-6s7 2.4 7 6" />
    </svg>
  );
}

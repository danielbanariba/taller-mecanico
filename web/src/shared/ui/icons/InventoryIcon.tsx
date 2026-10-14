export interface NavIconProps {
  className?: string;
}

/**
 * Open-box glyph for the Inventario tab. Purely decorative: the tab's
 * accessible name comes from its label text, never from this icon, so it
 * is always `aria-hidden` and never receives a programmatic name of its
 * own (no `<title>`, no `role="img"`).
 */
export function InventoryIcon({ className }: NavIconProps) {
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
      <path d="M3.5 7.5 12 3l8.5 4.5L12 12 3.5 7.5Z" />
      <path d="M3.5 7.5v9L12 21l8.5-4.5v-9" />
      <path d="M12 12v9" />
    </svg>
  );
}

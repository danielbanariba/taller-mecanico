import type { ReactNode } from "react";

export interface LetterPageStyleProps {
  children: ReactNode;
}

/**
 * Full-page `@page` rule: only a margin, so the browser's own Letter or
 * A4 default applies, unlike `ThermalPageStyle`'s measured size. Mirrors
 * `workorders/receipt/ReceiptLetterPage.tsx`'s rule, reimplemented here
 * without importing it (AD-16).
 */
export function LetterPageStyle({ children }: LetterPageStyleProps) {
  return (
    <>
      <style>{"@page { margin: 12mm; }"}</style>
      {children}
    </>
  );
}

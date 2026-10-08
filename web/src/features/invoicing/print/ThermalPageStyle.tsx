import { useLayoutEffect, useRef, useState, type ReactNode } from "react";

/** 1 CSS reference pixel is 1/96 inch; 1 inch is 25.4mm (the receipt's own AD-19 technique, reimplemented here). */
const PX_PER_MM = 96 / 25.4;

/**
 * Fallback page height used until the content's rendered height has been
 * measured: long enough that an unmeasured print is never cut off.
 */
const FALLBACK_PAGE_RULE = "@page { size: 58mm 297mm; margin: 0; }";

export interface ThermalPageStyleProps {
  children: ReactNode;
}

/**
 * Reimplements the non-fiscal receipt's measured-`@page`-height technique
 * (`workorders/receipt/Receipt58Page.tsx`) for the invoicing feature,
 * without importing it -- AD-16 keeps the receipt's own files untouched.
 *
 * Measures `children`'s rendered height at mount/update and emits a
 * matching `@page` rule, falling back to a tall default until that
 * measurement resolves: every jsdom render (jsdom has no layout engine,
 * so `getBoundingClientRect` always returns 0) and the instant between a
 * real browser's mount and its first measured paint.
 */
export function ThermalPageStyle({ children }: ThermalPageStyleProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [pageHeightMm, setPageHeightMm] = useState<number | null>(null);

  useLayoutEffect(() => {
    const node = rootRef.current;
    if (!node) {
      return;
    }
    const heightPx = node.getBoundingClientRect().height;
    if (heightPx > 0) {
      setPageHeightMm(heightPx / PX_PER_MM);
    }
  }, [children]);

  const pageRule = pageHeightMm !== null ? `@page { size: 58mm ${pageHeightMm}mm; margin: 0; }` : FALLBACK_PAGE_RULE;

  return (
    <>
      <style>{pageRule}</style>
      <div ref={rootRef} className="w-[48mm] font-mono text-[9pt]">
        {children}
      </div>
    </>
  );
}

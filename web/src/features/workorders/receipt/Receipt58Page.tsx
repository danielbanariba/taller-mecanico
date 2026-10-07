import { useLayoutEffect, useRef, useState } from "react";
import { useParams } from "react-router";

import { Alert } from "../../../shared/ui/Alert";
import { Button } from "../../../shared/ui/Button";
import { LinkButton } from "../../../shared/ui/LinkButton";
import { Spinner } from "../../../shared/ui/Spinner";
import { getWorkOrdersErrorMessage, workOrdersCopy } from "../copy";
import { ReceiptBody } from "./ReceiptBody";
import { useReceiptOrder } from "./useReceiptOrder";

/** 1 CSS reference pixel is 1/96 inch; 1 inch is 25.4mm (AD-19). */
const PX_PER_MM = 96 / 25.4;

/**
 * Fallback page height used until the content's rendered height has been
 * measured (AD-19): long enough that an unmeasured print is never cut off.
 */
const FALLBACK_PAGE_RULE = "@page { size: 58mm 297mm; margin: 0; }";

/**
 * 58 mm thermal receipt layout (the `non-fiscal-receipt` spec). Rendered
 * without the app shell (`design.md`'s AD-16, wired as a sibling route in
 * `app/router.tsx`), so no navigation chrome ever prints.
 *
 * The page's own `@page` height is measured from the rendered content at
 * mount (AD-19). A zero-or-unmeasured height -- every jsdom render (jsdom
 * has no layout engine, so `getBoundingClientRect` always returns 0), and
 * a real browser's instant between mount and its first measured paint --
 * keeps the fallback 297mm page instead of emitting an invalid
 * `58mm 0mm` rule that would print a blank or truncated receipt.
 */
export function Receipt58Page() {
  const { orderId: paramOrderId } = useParams<{ orderId: string }>();
  const orderId = paramOrderId ?? "";
  const state = useReceiptOrder(orderId);
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
  }, [state]);

  if (state.phase === "loading") {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (state.phase === "not-found") {
    return (
      <div className="flex flex-col gap-4 p-4">
        <Alert variant="error">{getWorkOrdersErrorMessage(state.errorCode)}</Alert>
        <LinkButton to="/ordenes" variant="secondary">
          {workOrdersCopy.detail.backToList}
        </LinkButton>
      </div>
    );
  }

  const pageRule = pageHeightMm !== null ? `@page { size: 58mm ${pageHeightMm}mm; margin: 0; }` : FALLBACK_PAGE_RULE;

  return (
    <div className="flex flex-col gap-4 p-4">
      <style>{pageRule}</style>
      <Button variant="secondary" onClick={() => window.print()} className="print:hidden">
        {workOrdersCopy.receipt.print}
      </Button>
      {state.phase === "not-eligible" ? (
        <Alert variant="info">{workOrdersCopy.receipt.notEligible}</Alert>
      ) : (
        <div ref={rootRef} className="w-[48mm] font-mono text-[9pt]">
          <ReceiptBody order={state.order} />
        </div>
      )}
    </div>
  );
}

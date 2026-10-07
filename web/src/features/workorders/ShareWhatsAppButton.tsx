import { lazy, Suspense, useState } from "react";

import { Button } from "../../shared/ui/Button";
import { BUTTON_VARIANT_CLASSES } from "../../shared/ui/buttonVariants";
import { Spinner } from "../../shared/ui/Spinner";
import { workOrdersCopy } from "./copy";
import { buildOrderSummary, buildWhatsAppUrl, supportsFileShare } from "./whatsapp";
import type { WorkOrderOut } from "./api";

// Loaded only once a mechanic actually opens it (`design.md`'s "Lazy
// boundaries" note), never on every order-detail render.
const ShareSheet = lazy(() => import("./share/ShareSheet").then((module) => ({ default: module.ShareSheet })));

export interface ShareWhatsAppButtonProps {
  order: WorkOrderOut;
  workshopName: string;
}

/**
 * "Compartir por WhatsApp" (the `whatsapp-sharing` spec): visible only
 * for a customer with a mobile phone recorded. Where the browser cannot
 * share files, this is a plain anchor straight to the prefilled `wa.me`
 * link; where it can, tapping it loads the lazy `ShareSheet` to let the
 * mechanic optionally attach photos first (`design.md`'s AD-18).
 */
export function ShareWhatsAppButton({ order, workshopName }: ShareWhatsAppButtonProps) {
  const [sheetOpen, setSheetOpen] = useState(false);

  if (order.customer.phone_is_mobile !== true || !order.customer.phone) {
    return null;
  }

  const summary = buildOrderSummary(order, workshopName);
  const url = buildWhatsAppUrl(order.customer.phone, summary);

  if (!supportsFileShare()) {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className={`inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl px-4 text-lg font-semibold transition-colors ${BUTTON_VARIANT_CLASSES.secondary}`}
      >
        {workOrdersCopy.share.shareButton}
      </a>
    );
  }

  return (
    <>
      <Button variant="secondary" onClick={() => setSheetOpen(true)}>
        {workOrdersCopy.share.shareButton}
      </Button>
      {sheetOpen ? (
        <Suspense fallback={<Spinner />}>
          <ShareSheet url={url} summary={summary} onClose={() => setSheetOpen(false)} />
        </Suspense>
      ) : null}
    </>
  );
}

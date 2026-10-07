import { useParams } from "react-router";

import { Alert } from "../../../shared/ui/Alert";
import { Button } from "../../../shared/ui/Button";
import { LinkButton } from "../../../shared/ui/LinkButton";
import { Spinner } from "../../../shared/ui/Spinner";
import { getWorkOrdersErrorMessage, workOrdersCopy } from "../copy";
import { ReceiptBody } from "./ReceiptBody";
import { useReceiptOrder } from "./useReceiptOrder";

/**
 * Full-page receipt layout (the `non-fiscal-receipt` spec). Rendered
 * without the app shell, the same way `Receipt58Page` is (`design.md`'s
 * AD-16). Its `@page` rule sets only a margin and no `size`, so the
 * browser's own Letter or A4 default applies (AD-19) -- unlike the 58 mm
 * layout, which measures and sets its own page size.
 */
export function ReceiptLetterPage() {
  const { orderId: paramOrderId } = useParams<{ orderId: string }>();
  const orderId = paramOrderId ?? "";
  const state = useReceiptOrder(orderId);

  if (state.phase === "loading") {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (state.phase === "not-found") {
    return (
      <div className="flex flex-col gap-4 p-6">
        <Alert variant="error">{getWorkOrdersErrorMessage(state.errorCode)}</Alert>
        <LinkButton to="/ordenes" variant="secondary">
          {workOrdersCopy.detail.backToList}
        </LinkButton>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 p-6">
      <style>{"@page { margin: 12mm; }"}</style>
      <Button variant="secondary" onClick={() => window.print()} className="print:hidden">
        {workOrdersCopy.receipt.print}
      </Button>
      {state.phase === "not-eligible" ? (
        <Alert variant="info">{workOrdersCopy.receipt.notEligible}</Alert>
      ) : (
        <ReceiptBody order={state.order} />
      )}
    </div>
  );
}

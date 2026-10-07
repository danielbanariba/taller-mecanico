import { ApiError } from "../../../shared/api/http";
import { useWorkOrder } from "../hooks";
import type { WorkOrderOut } from "../api";

export type ReceiptOrderState =
  | { phase: "loading" }
  | { phase: "not-found"; errorCode: string }
  | { phase: "not-eligible"; order: WorkOrderOut }
  | { phase: "ready"; order: WorkOrderOut };

/** The only statuses the `non-fiscal-receipt` spec allows a receipt to expose. */
const RECEIPT_ELIGIBLE_STATUSES = new Set<WorkOrderOut["status"]>(["completed", "delivered"]);

/**
 * Whether `status` may be exposed through either receipt route. Exported
 * so `WorkOrderDetailPage` can gate its own receipt links on the exact
 * same rule instead of duplicating this status list -- a duplicated list
 * could drift and either hide the links for an eligible order or offer a
 * receipt for one the route itself would then refuse to render.
 */
export function isReceiptEligible(status: WorkOrderOut["status"]): boolean {
  return RECEIPT_ELIGIBLE_STATUSES.has(status);
}

/**
 * Shared gating for both printable layouts (`Receipt58Page`,
 * `ReceiptLetterPage`): the loading/not-found handling is identical to
 * `WorkOrderDetailPage`'s, plus the receipt-only rule that a work order's
 * data is only ever exposed through a receipt route once it is
 * `completed` or `delivered` (the `non-fiscal-receipt` spec's "A Receipt
 * Is Only Available For Completed Or Delivered Orders"). Extracted once,
 * instead of duplicated in each layout component, so the eligibility rule
 * can only drift from the spec in one place.
 */
export function useReceiptOrder(orderId: string): ReceiptOrderState {
  const order = useWorkOrder(orderId);

  if (order.isPending) {
    return { phase: "loading" };
  }

  // A failed refetch keeps the cached order in `order.data`; only the
  // server saying the order is gone replaces it (mirrors
  // `WorkOrderDetailPage`'s same not-found handling).
  const isNotFound = order.error instanceof ApiError && order.error.status === 404;
  if (isNotFound || !order.data) {
    const errorCode = order.error instanceof ApiError ? order.error.code : "work_order_not_found";
    return { phase: "not-found", errorCode };
  }

  if (!isReceiptEligible(order.data.status)) {
    return { phase: "not-eligible", order: order.data };
  }

  return { phase: "ready", order: order.data };
}

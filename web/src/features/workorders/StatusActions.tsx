import { useState } from "react";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Dialog } from "../../shared/ui/Dialog";
import { getWorkOrdersErrorMessage, statusActionLabel, workOrdersCopy } from "./copy";
import { useChangeStatus } from "./hooks";
import type { WorkOrderOut } from "./api";

export interface StatusActionsProps {
  order: WorkOrderOut;
}

/**
 * One button per `order.allowed_transitions` -- never a client-side
 * transition table, so the web can never drift from the server's own
 * acyclic state machine (`design.md`'s AD-7: "The response carries
 * `allowed_transitions`, so the web never duplicates the transition
 * table"). Renders nothing once the order has no further transition
 * (`delivered`/`cancelled`).
 *
 * Forward transitions always render before cancellation (never the
 * server's own alphabetical `allowed_transitions` order, which sorts
 * "cancelled" ahead of "in_progress"/"completed"). Cancellation is
 * terminal -- a cancelled order can never reopen, and cancelling an
 * `in_progress` order reverses stock it already consumed -- so tapping it
 * only opens a confirmation dialog; the status request itself fires only
 * from that dialog's own confirm button.
 */
export function StatusActions({ order }: StatusActionsProps) {
  const isOffline = useOnlineStatus();
  const changeStatus = useChangeStatus(order.id);
  const [cancelConfirmOpen, setCancelConfirmOpen] = useState(false);

  if (order.allowed_transitions.length === 0) {
    return null;
  }

  const rawErrorCode = changeStatus.error instanceof ApiError ? changeStatus.error.code : undefined;
  // A `useMutation`'s error only clears on a new `mutate()` call or an
  // explicit `reset()`; neither happens here on its own, so a
  // `work_order_has_payments` 409 from an earlier cancel attempt would
  // otherwise linger on screen forever. Voiding the blocking payment (in
  // `PaymentList`, a sibling under `WorkOrderDetailPage`) updates this
  // same `order` prop with no non-voided payments left, so deriving the
  // displayed message from that current state -- instead of from the
  // mutation's own stale error -- clears it the moment voiding succeeds.
  const hasBlockingPayment = order.payments.some((payment) => payment.voided_at === null);
  const errorMessage =
    rawErrorCode && !(rawErrorCode === "work_order_has_payments" && !hasBlockingPayment)
      ? getWorkOrdersErrorMessage(rawErrorCode)
      : undefined;

  const forwardTransitions = order.allowed_transitions.filter((target) => target !== "cancelled");
  const canCancel = order.allowed_transitions.includes("cancelled");
  const cancelling = changeStatus.isPending && changeStatus.variables?.status === "cancelled";

  function handleCancelConfirm() {
    changeStatus.mutate({ status: "cancelled" }, { onSuccess: () => setCancelConfirmOpen(false) });
  }

  return (
    <div className="flex flex-col gap-2">
      {isOffline ? <Alert variant="info">{workOrdersCopy.offline.statusChangeDisabled}</Alert> : null}
      {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
      <div className="flex flex-wrap gap-3">
        {forwardTransitions.map((target) => (
          <Button
            key={target}
            variant="primary"
            onClick={() => changeStatus.mutate({ status: target })}
            loading={changeStatus.isPending && changeStatus.variables?.status === target}
            disabled={isOffline || changeStatus.isPending}
            fullWidth={false}
            className="px-4"
          >
            {statusActionLabel(target)}
          </Button>
        ))}
        {canCancel ? (
          <Button
            variant="destructive"
            onClick={() => setCancelConfirmOpen(true)}
            loading={cancelling}
            disabled={isOffline || changeStatus.isPending}
            fullWidth={false}
            className="px-4"
          >
            {statusActionLabel("cancelled")}
          </Button>
        ) : null}
      </div>

      <Dialog
        open={cancelConfirmOpen}
        title={workOrdersCopy.cancelConfirm.title}
        onClose={() => setCancelConfirmOpen(false)}
      >
        <div className="flex flex-col gap-4">
          <p className="text-base text-brand-foreground">{workOrdersCopy.cancelConfirm.body}</p>
          {order.status === "in_progress" ? (
            <p className="text-base text-brand-foreground">{workOrdersCopy.cancelConfirm.bodyInProgress}</p>
          ) : null}
          {isOffline ? <Alert variant="info">{workOrdersCopy.offline.statusChangeDisabled}</Alert> : null}
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setCancelConfirmOpen(false)}>
              {workOrdersCopy.cancelConfirm.keep}
            </Button>
            <Button
              variant="destructive"
              onClick={handleCancelConfirm}
              loading={cancelling}
              disabled={isOffline || changeStatus.isPending}
            >
              {workOrdersCopy.cancelConfirm.confirm}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

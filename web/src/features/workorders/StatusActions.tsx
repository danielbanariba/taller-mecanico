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

  const errorMessage =
    changeStatus.error instanceof ApiError ? getWorkOrdersErrorMessage(changeStatus.error.code) : undefined;

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
            className="w-auto px-4"
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
            className="w-auto px-4"
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

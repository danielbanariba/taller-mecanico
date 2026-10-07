import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
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
 */
export function StatusActions({ order }: StatusActionsProps) {
  const isOffline = useOnlineStatus();
  const changeStatus = useChangeStatus(order.id);

  if (order.allowed_transitions.length === 0) {
    return null;
  }

  const errorMessage =
    changeStatus.error instanceof ApiError ? getWorkOrdersErrorMessage(changeStatus.error.code) : undefined;

  return (
    <div className="flex flex-col gap-2">
      {isOffline ? <Alert variant="info">{workOrdersCopy.offline.statusChangeDisabled}</Alert> : null}
      {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
      <div className="flex flex-wrap gap-3">
        {order.allowed_transitions.map((target) => (
          <Button
            key={target}
            variant={target === "cancelled" ? "destructive" : "primary"}
            onClick={() => changeStatus.mutate({ status: target })}
            loading={changeStatus.isPending && changeStatus.variables?.status === target}
            disabled={isOffline || changeStatus.isPending}
            className="w-auto px-4"
          >
            {statusActionLabel(target)}
          </Button>
        ))}
      </div>
    </div>
  );
}

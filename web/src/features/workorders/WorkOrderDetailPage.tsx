import { useParams } from "react-router";

import { ApiError } from "../../shared/api/http";
import { formatCents } from "../../shared/format/money";
import { Alert } from "../../shared/ui/Alert";
import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { getWorkOrdersErrorMessage, statusLabel, workOrdersCopy } from "./copy";
import { useWorkOrder } from "./hooks";
import { WorkOrderLines } from "./WorkOrderLines";

/**
 * Container: the read-only order detail -- vehicle, customer, lines and
 * total. Status actions, WhatsApp sharing, the line editor and payments
 * are wired in later slices (S5/S6/P3).
 */
export function WorkOrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const orderId = id ?? "";
  const order = useWorkOrder(orderId);

  if (order.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // A failed refetch keeps the cached order in `order.data` (e.g. after a
  // reload offline); only the server saying the order is gone replaces it.
  const isNotFound = order.error instanceof ApiError && order.error.status === 404;
  if (isNotFound || !order.data) {
    const errorCode = order.error instanceof ApiError ? order.error.code : "work_order_not_found";
    return (
      <div className="flex flex-col gap-4">
        <Alert variant="error">{getWorkOrdersErrorMessage(errorCode)}</Alert>
        <LinkButton to="/ordenes" variant="secondary">
          {workOrdersCopy.detail.backToList}
        </LinkButton>
      </div>
    );
  }

  const data = order.data;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-brand-primary">{workOrdersCopy.detail.orderTitle(data.number)}</h1>
        <p className="text-sm text-brand-muted-foreground">
          {[data.vehicle.make, data.vehicle.model].filter(Boolean).join(" ")}
          {data.vehicle.plate ? ` · ${data.vehicle.plate}` : ""}
        </p>
        <p className="text-base text-brand-foreground">{data.customer.full_name}</p>
        <p className="text-base font-semibold text-brand-primary">{statusLabel(data.status)}</p>
      </header>

      {data.complaint ? (
        <p className="text-base text-brand-foreground">
          <span className="font-semibold">{workOrdersCopy.detail.complaintLabel}: </span>
          {data.complaint}
        </p>
      ) : null}

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-bold text-brand-primary">{workOrdersCopy.detail.linesTitle}</h2>
        <WorkOrderLines lines={data.lines} />
        <p className="flex items-center justify-between text-lg font-bold text-brand-foreground">
          <span>{workOrdersCopy.detail.totalLabel}</span>
          <span>{formatCents(data.total_cents)}</span>
        </p>
      </section>
    </div>
  );
}

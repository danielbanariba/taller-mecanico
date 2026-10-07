import { statusLabel, workOrdersCopy } from "./copy";
import { formatCents } from "../../shared/format/money";
import type { WorkOrderSummaryOut } from "./api";

export interface WorkOrderListProps {
  orders: WorkOrderSummaryOut[];
  onOpen: (order: WorkOrderSummaryOut) => void;
}

/** Presentational: one status group's work orders, with an empty state. */
export function WorkOrderList({ orders, onOpen }: WorkOrderListProps) {
  if (orders.length === 0) {
    return (
      <div className="flex flex-col items-center gap-1 rounded-2xl border border-dashed border-brand-border px-4 py-10 text-center">
        <p className="text-lg font-semibold text-brand-foreground">{workOrdersCopy.list.emptyTitle}</p>
        <p className="text-base text-brand-muted-foreground">{workOrdersCopy.list.emptyBody}</p>
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-2">
      {orders.map((order) => (
        <li key={order.id}>
          <button
            type="button"
            onClick={() => onOpen(order)}
            className="flex w-full flex-col items-start gap-0.5 rounded-2xl border border-brand-border bg-brand-card px-4 py-3 text-left"
          >
            <span className="text-lg font-semibold text-brand-foreground">
              {workOrdersCopy.detail.orderTitle(order.number)}
            </span>
            <span className="text-sm text-brand-muted-foreground">
              {[order.vehicle.make, order.vehicle.model].filter(Boolean).join(" ")}
              {order.vehicle.plate ? ` · ${order.vehicle.plate}` : ""}
              {" · "}
              {order.customer.full_name}
            </span>
            <span className="flex w-full items-center justify-between">
              <span className="text-sm font-medium text-brand-primary">{statusLabel(order.status)}</span>
              <span className="text-sm font-semibold text-brand-foreground">{formatCents(order.total_cents)}</span>
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

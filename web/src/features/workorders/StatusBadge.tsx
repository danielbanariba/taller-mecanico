import { statusLabel } from "./copy";
import type { WorkOrderStatus } from "./api";

export interface StatusBadgeProps {
  status: WorkOrderStatus;
}

/**
 * One background/text color pair per `WorkOrderStatus`, from Tailwind's
 * `-100`/`-700`+ scale for contrast that holds up on a bright phone screen
 * -- the same pairing `ItemRow`'s own badges use (`bg-amber-100
 * text-amber-800`), reusing the shared `brand-destructive` token for
 * `cancelled` the way `ItemRow`'s "needs review" badge does.
 */
const STATUS_BADGE_CLASSES: Record<WorkOrderStatus, string> = {
  quote: "bg-slate-100 text-slate-700",
  approved: "bg-blue-100 text-blue-800",
  in_progress: "bg-amber-100 text-amber-800",
  completed: "bg-emerald-100 text-emerald-800",
  delivered: "bg-violet-100 text-violet-800",
  cancelled: "bg-red-100 text-brand-destructive",
};

/**
 * Atomic, presentational: a work order's status as a colored chip, reusing
 * `statusLabel`'s existing Spanish copy so the label is never duplicated.
 * Used wherever a status shows: the orders list, the order detail screen,
 * and -- through `WorkOrderList` -- the customer's and vehicle's own order
 * history.
 */
export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_BADGE_CLASSES[status]}`}>
      {statusLabel(status)}
    </span>
  );
}

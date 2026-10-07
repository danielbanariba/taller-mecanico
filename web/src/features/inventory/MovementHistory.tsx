import { Link } from "react-router";

import type { MovementOut } from "./api";
import { formatDateTime } from "./format";
import { inventoryCopy, movementLabel } from "./copy";

export interface MovementHistoryProps {
  movements: MovementOut[];
}

/** Presentational: renders movements in the order given (newest first, per the API contract). */
export function MovementHistory({ movements }: MovementHistoryProps) {
  if (movements.length === 0) {
    return <p className="text-base text-brand-muted-foreground">{inventoryCopy.detail.historyEmpty}</p>;
  }

  return (
    <ul className="flex flex-col gap-2">
      {movements.map((movement) => (
        <li
          key={movement.id}
          className="flex items-center justify-between rounded-xl border border-brand-border bg-brand-card px-4 py-3"
        >
          <span className="text-base font-semibold text-brand-foreground">{movementLabel(movement)}</span>
          <span className="flex flex-col items-end gap-0.5">
            {movement.order_number != null && movement.order_id != null ? (
              <Link to={`/ordenes/${movement.order_id}`} className="text-sm font-medium text-brand-primary">
                {inventoryCopy.detail.orderLink(movement.order_number)}
              </Link>
            ) : null}
            <span className="text-sm text-brand-muted-foreground">{formatDateTime(movement.occurred_at)}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

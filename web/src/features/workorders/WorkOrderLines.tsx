import { lineKindLabel, workOrdersCopy } from "./copy";
import { formatCents } from "../../shared/format/money";
import type { WorkOrderLineOut } from "./api";

export interface WorkOrderLinesProps {
  lines: WorkOrderLineOut[];
}

/** Presentational, read-only in this slice: a work order's quote lines. Status actions and editing arrive in later slices. */
export function WorkOrderLines({ lines }: WorkOrderLinesProps) {
  if (lines.length === 0) {
    return <p className="text-base text-brand-muted-foreground">{workOrdersCopy.detail.linesEmpty}</p>;
  }

  return (
    <ul className="flex flex-col gap-2">
      {lines.map((line) => (
        <li
          key={line.id}
          className="flex items-center justify-between rounded-xl border border-brand-border bg-brand-card px-4 py-3"
        >
          <span className="flex flex-col">
            <span className="text-base font-semibold text-brand-foreground">{line.description}</span>
            <span className="text-sm text-brand-muted-foreground">
              {lineKindLabel(line.kind)} · {line.quantity} × {formatCents(line.unit_price_cents)}
            </span>
          </span>
          <span className="text-base font-semibold text-brand-foreground">{formatCents(line.line_total_cents)}</span>
        </li>
      ))}
    </ul>
  );
}

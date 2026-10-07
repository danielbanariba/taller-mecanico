import { lineKindLabel, workOrdersCopy } from "./copy";
import { formatCents } from "../../shared/format/money";
import { Button } from "../../shared/ui/Button";
import type { WorkOrderLineOut } from "./api";

export interface WorkOrderLinesProps {
  lines: WorkOrderLineOut[];
  /** Whether the order's own status allows line edits (`order.lines_editable`). */
  editable: boolean;
  /** Disables the edit/remove buttons without hiding them (e.g. offline), matching every other write control's convention in this app. */
  disabled?: boolean;
  onEdit: (line: WorkOrderLineOut) => void;
  onRemove: (line: WorkOrderLineOut) => void;
  /** The line currently being removed, for its own button's loading state. */
  removingLineId?: string;
}

/** A work order's quote lines, with edit/remove actions once the order allows line edits. */
export function WorkOrderLines({
  lines,
  editable,
  disabled = false,
  onEdit,
  onRemove,
  removingLineId,
}: WorkOrderLinesProps) {
  if (lines.length === 0) {
    return <p className="text-base text-brand-muted-foreground">{workOrdersCopy.detail.linesEmpty}</p>;
  }

  return (
    <ul className="flex flex-col gap-2">
      {lines.map((line) => {
        const removing = removingLineId === line.id;
        return (
          <li key={line.id} className="flex flex-col gap-2 rounded-xl border border-brand-border bg-brand-card px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="flex flex-col">
                <span className="text-base font-semibold text-brand-foreground">{line.description}</span>
                <span className="text-sm text-brand-muted-foreground">
                  {lineKindLabel(line.kind)} · {line.quantity} × {formatCents(line.unit_price_cents)}
                </span>
              </span>
              <span className="text-base font-semibold text-brand-foreground">
                {formatCents(line.line_total_cents)}
              </span>
            </div>
            {editable ? (
              <div className="flex gap-3">
                <Button variant="secondary" onClick={() => onEdit(line)} disabled={disabled || removing}>
                  {workOrdersCopy.lineEditor.editLine}
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => onRemove(line)}
                  loading={removing}
                  disabled={disabled || removing}
                >
                  {workOrdersCopy.lineEditor.removeLine}
                </Button>
              </div>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

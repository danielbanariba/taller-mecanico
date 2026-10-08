import { invoicingCopy, rangeStateLabel } from "../copy";
import type { CaiRangeOut } from "../api";

export interface CaiRangeListProps {
  ranges: CaiRangeOut[];
}

/**
 * Presentational: every registered CAI range for this workshop, each
 * with its own derived state (AD-4), remaining numbers and formatted
 * bounds. Ranges are never deleted, so this list only ever grows.
 */
export function CaiRangeList({ ranges }: CaiRangeListProps) {
  if (ranges.length === 0) {
    return <p className="text-base text-brand-muted-foreground">{invoicingCopy.settings.noRanges}</p>;
  }

  return (
    <ul className="flex flex-col gap-2">
      {ranges.map((range) => (
        <li key={range.id} className="flex flex-col gap-1 rounded-xl border border-brand-border p-3">
          <p className="flex items-center justify-between gap-2 font-semibold text-brand-foreground">
            <span>{range.cai}</span>
            <span>{rangeStateLabel(range.state)}</span>
          </p>
          <p className="text-sm text-brand-muted-foreground">
            {range.first_number} – {range.last_number} · {invoicingCopy.settings.remainingLabel(range.remaining)}
          </p>
          <p className="text-sm text-brand-muted-foreground">
            {invoicingCopy.settings.deadlineLabel(range.issue_deadline)}
          </p>
        </li>
      ))}
    </ul>
  );
}

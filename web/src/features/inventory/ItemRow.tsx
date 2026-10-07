import type { ItemOut } from "./api";
import { inventoryCopy } from "./copy";

export interface ItemRowProps {
  item: ItemOut;
  onOpen: () => void;
  onIncrement: () => void;
  onDecrement: () => void;
}

/**
 * Presentational: one row of the inventory list. The name/category area is
 * its own button so tapping the row opens the detail screen, while the
 * stepper buttons sit outside it and never trigger that navigation.
 */
export function ItemRow({ item, onOpen, onIncrement, onDecrement }: ItemRowProps) {
  const subtitle = [item.category, item.unit].filter(Boolean).join(" · ");
  const badgeLabel = item.needs_review
    ? inventoryCopy.badges.needsReview
    : item.is_low
      ? inventoryCopy.badges.lowStock
      : null;
  const badgeClassName = item.needs_review
    ? "bg-red-100 text-brand-destructive"
    : "bg-amber-100 text-amber-800";

  return (
    <li className="flex items-center gap-3 rounded-2xl border border-brand-border bg-brand-card p-3">
      <button type="button" onClick={onOpen} className="flex flex-1 flex-col items-start gap-1 text-left">
        <span className="text-lg font-semibold text-brand-foreground">{item.name}</span>
        {subtitle ? <span className="text-sm text-brand-muted-foreground">{subtitle}</span> : null}
        {badgeLabel ? (
          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${badgeClassName}`}>
            {badgeLabel}
          </span>
        ) : null}
      </button>
      <div className="flex flex-col items-center gap-2">
        <span className="text-3xl font-bold tabular-nums text-brand-primary">{item.stock}</span>
        <div className="flex gap-2">
          <button
            type="button"
            aria-label={inventoryCopy.list.decrementLabel(item.name)}
            onClick={onDecrement}
            className="flex h-14 w-14 items-center justify-center rounded-xl bg-brand-muted text-2xl font-bold text-brand-primary active:bg-brand-border"
          >
            −
          </button>
          <button
            type="button"
            aria-label={inventoryCopy.list.incrementLabel(item.name)}
            onClick={onIncrement}
            className="flex h-14 w-14 items-center justify-center rounded-xl bg-brand-accent text-2xl font-bold text-brand-on-accent active:bg-brand-secondary"
          >
            +
          </button>
        </div>
      </div>
    </li>
  );
}

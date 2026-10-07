import { useEffect, useState } from "react";

import { formatCents } from "../../shared/format/money";
import { Spinner } from "../../shared/ui/Spinner";
import { TextField } from "../../shared/ui/TextField";
import { useItems } from "../inventory/hooks";
import { workOrdersCopy } from "./copy";
import type { ItemOut } from "../inventory/api";

const SEARCH_DEBOUNCE_MS = 300;

/** Debounces `value`, settling `delayMs` after the last change (mirrors the equivalent hook in `inventory/hooks.ts` and `customers/hooks.ts`; kept local since neither is shared yet). */
function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

export interface ItemPickerProps {
  onSelect: (item: ItemOut) => void;
}

/**
 * Searches the workshop's active items and lets the mechanic pick one for
 * an inventory-part line. Reuses inventory's own `useItems` read -- a pure
 * query, never a mutation -- so browsing here can never move stock ahead
 * of the line actually being saved (the `work-orders` spec's own rule:
 * adding a part line posts no movement until `work-order-stock-consumption`
 * says so).
 */
export function ItemPicker({ onSelect }: ItemPickerProps) {
  const [searchInput, setSearchInput] = useState("");
  const debouncedQuery = useDebouncedValue(searchInput, SEARCH_DEBOUNCE_MS);
  const items = useItems({ q: debouncedQuery.trim() || undefined });
  const results = items.data ?? [];

  return (
    <div className="flex flex-col gap-3">
      <TextField
        label={workOrdersCopy.itemPicker.searchLabel}
        placeholder={workOrdersCopy.itemPicker.searchPlaceholder}
        value={searchInput}
        onChange={(event) => setSearchInput(event.target.value)}
      />
      {items.isPending ? (
        <div className="flex justify-center py-6">
          <Spinner />
        </div>
      ) : results.length === 0 ? (
        <p className="text-base text-brand-muted-foreground">{workOrdersCopy.itemPicker.emptyTitle}</p>
      ) : (
        <ul className="flex max-h-72 flex-col gap-2 overflow-y-auto">
          {results.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => onSelect(item)}
                className="flex w-full flex-col items-start gap-0.5 rounded-xl border border-brand-border bg-brand-card px-4 py-3 text-left"
              >
                <span className="text-base font-semibold text-brand-foreground">{item.name}</span>
                <span className="text-sm text-brand-muted-foreground">
                  {item.category ? `${item.category} · ` : ""}
                  {`Stock ${item.stock}`}
                  {item.sale_price_cents != null ? ` · ${formatCents(item.sale_price_cents)}` : ""}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

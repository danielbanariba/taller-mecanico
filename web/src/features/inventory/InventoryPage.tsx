import { useCallback, useMemo, useState } from "react";
import { useNavigate } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Chip } from "../../shared/ui/Chip";
import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { TextField } from "../../shared/ui/TextField";
import { getInventoryErrorMessage, inventoryCopy } from "./copy";
import { useDebouncedValue, useItems, useRecordMovement } from "./hooks";
import { ItemList } from "./ItemList";
import type { ItemOut } from "./api";

type InventoryFilter = "all" | "low" | "needsReview";

const SEARCH_DEBOUNCE_MS = 300;

/** Container: the inventory list, search, filters and the stock stepper. */
export function InventoryPage() {
  const navigate = useNavigate();
  const recordMovement = useRecordMovement();

  const [searchInput, setSearchInput] = useState("");
  const [filter, setFilter] = useState<InventoryFilter>("all");
  const debouncedQuery = useDebouncedValue(searchInput, SEARCH_DEBOUNCE_MS);

  const items = useItems({
    q: debouncedQuery.trim() || undefined,
    lowStock: filter === "low" ? true : undefined,
  });
  const isOffline = useOnlineStatus();
  // No cached data AND the reason is connectivity: either already offline,
  // or the first fetch already settled into `network_error`. Without this,
  // a cold load that starts offline falls through to the empty state --
  // indistinguishable from a workshop that genuinely has none (the same
  // QA sweep finding as `CustomersPage` and `NewWorkOrderPage`).
  const itemsUnavailable =
    items.data === undefined &&
    (isOffline || (items.error instanceof ApiError && items.error.code === "network_error"));

  const visibleItems = useMemo(() => {
    const list = items.data ?? [];
    return filter === "needsReview" ? list.filter((item) => item.needs_review) : list;
  }, [items.data, filter]);

  // `mutate` itself is stable across renders (TanStack Query's own
  // `useCallback`, keyed only on the mutation observer instance) even
  // though `recordMovement` is a fresh object every render; destructuring
  // it out keeps the dependency array -- and `react-hooks/exhaustive-deps`
  // -- honest, instead of depending on the whole (unstable) object.
  const { mutate: recordStockMovement } = recordMovement;

  // Stable across renders, so every row in `ItemList` receives the exact
  // same function -- required for `ItemRow`'s `memo` to actually skip
  // re-rendering untapped rows; see `ItemRow.tsx`'s own comment.
  const handleOpen = useCallback((item: ItemOut) => navigate(`/inventario/${item.id}`), [navigate]);
  const handleIncrement = useCallback(
    (item: ItemOut) => recordStockMovement({ itemId: item.id, kind: "in", quantity: 1 }),
    [recordStockMovement],
  );
  const handleDecrement = useCallback(
    (item: ItemOut) => recordStockMovement({ itemId: item.id, kind: "out", quantity: 1 }),
    [recordStockMovement],
  );

  const movementErrorMessage =
    recordMovement.error instanceof ApiError ? getInventoryErrorMessage(recordMovement.error.code) : undefined;
  const isFiltered = filter !== "all" || debouncedQuery.trim().length > 0;

  return (
    <>
      {movementErrorMessage ? <Alert variant="error">{movementErrorMessage}</Alert> : null}

      <TextField
        label={inventoryCopy.list.searchLabel}
        placeholder={inventoryCopy.list.searchPlaceholder}
        value={searchInput}
        onChange={(event) => setSearchInput(event.target.value)}
      />

      <div role="group" aria-label={inventoryCopy.list.filterGroupLabel} className="flex gap-2">
        <Chip active={filter === "all"} onClick={() => setFilter("all")}>
          {inventoryCopy.list.filterAll}
        </Chip>
        <Chip active={filter === "low"} onClick={() => setFilter("low")}>
          {inventoryCopy.list.filterLow}
        </Chip>
        <Chip active={filter === "needsReview"} onClick={() => setFilter("needsReview")}>
          {inventoryCopy.list.filterNeedsReview}
        </Chip>
      </div>

      <Button onClick={() => navigate("/inventario/nuevo")}>{inventoryCopy.list.addItem}</Button>
      <LinkButton to="/inventario/archivados" variant="secondary">
        {inventoryCopy.list.viewArchived}
      </LinkButton>

      {itemsUnavailable ? (
        <Alert variant="info">{inventoryCopy.offline.listUnavailable}</Alert>
      ) : items.isPending ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : visibleItems.length === 0 ? (
        <div className="flex flex-col items-center gap-1 rounded-2xl border border-dashed border-brand-border px-4 py-10 text-center">
          <p className="text-lg font-semibold text-brand-foreground">
            {isFiltered ? inventoryCopy.list.emptyFilteredTitle : inventoryCopy.list.emptyTitle}
          </p>
          <p className="text-base text-brand-muted-foreground">
            {isFiltered ? inventoryCopy.list.emptyFilteredBody : inventoryCopy.list.emptyBody}
          </p>
        </div>
      ) : (
        <ItemList
          items={visibleItems}
          onOpen={handleOpen}
          onIncrement={handleIncrement}
          onDecrement={handleDecrement}
        />
      )}
    </>
  );
}

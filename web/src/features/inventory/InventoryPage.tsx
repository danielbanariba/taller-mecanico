import { useMemo, useState } from "react";
import { useNavigate } from "react-router";

import { ApiError } from "../../shared/api/http";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Chip } from "../../shared/ui/Chip";
import { Spinner } from "../../shared/ui/Spinner";
import { TextField } from "../../shared/ui/TextField";
import { authCopy } from "../auth/copy";
import { useLogout, useSession } from "../auth/hooks";
import { getInventoryErrorMessage, inventoryCopy } from "./copy";
import { useDebouncedValue, useItems, useRecordMovement } from "./hooks";
import { ItemRow } from "./ItemRow";
import type { ItemOut } from "./api";

type InventoryFilter = "all" | "low" | "needsReview";

const SEARCH_DEBOUNCE_MS = 300;

/** Container: the inventory list, search, filters and the stock stepper. */
export function InventoryPage() {
  const navigate = useNavigate();
  const session = useSession();
  const logout = useLogout();
  const recordMovement = useRecordMovement();

  const [searchInput, setSearchInput] = useState("");
  const [filter, setFilter] = useState<InventoryFilter>("all");
  const debouncedQuery = useDebouncedValue(searchInput, SEARCH_DEBOUNCE_MS);

  const items = useItems({
    q: debouncedQuery.trim() || undefined,
    lowStock: filter === "low" ? true : undefined,
  });

  const visibleItems = useMemo(() => {
    const list = items.data ?? [];
    return filter === "needsReview" ? list.filter((item) => item.needs_review) : list;
  }, [items.data, filter]);

  function handleLogout() {
    logout.mutate(undefined, {
      onSuccess: () => navigate("/login", { replace: true }),
    });
  }

  function handleIncrement(item: ItemOut) {
    recordMovement.mutate({ itemId: item.id, kind: "in", quantity: 1 });
  }

  function handleDecrement(item: ItemOut) {
    recordMovement.mutate({ itemId: item.id, kind: "out", quantity: 1 });
  }

  const movementErrorMessage =
    recordMovement.error instanceof ApiError ? getInventoryErrorMessage(recordMovement.error.code) : undefined;
  const isFiltered = filter !== "all" || debouncedQuery.trim().length > 0;

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-4 px-4 py-6">
      <header className="flex flex-col gap-3">
        <h1 className="text-2xl font-bold text-brand-primary">{session.data?.workshop.name}</h1>
        <Button variant="secondary" onClick={handleLogout} loading={logout.isPending}>
          {authCopy.logout.submit}
        </Button>
      </header>

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

      {items.isPending ? (
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
        <ul className="flex flex-col gap-2">
          {visibleItems.map((item) => (
            <ItemRow
              key={item.id}
              item={item}
              onOpen={() => navigate(`/inventario/${item.id}`)}
              onIncrement={() => handleIncrement(item)}
              onDecrement={() => handleDecrement(item)}
            />
          ))}
        </ul>
      )}
    </main>
  );
}

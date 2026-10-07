import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { ApiError } from "../../shared/api/http";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Dialog } from "../../shared/ui/Dialog";
import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { TextField } from "../../shared/ui/TextField";
import { getInventoryErrorMessage, inventoryCopy } from "./copy";
import { formatCents, MAX_STOCK, parseStockQuantity } from "./format";
import { useArchiveItem, useItem, useMovements, useRecordMovement } from "./hooks";
import { MovementHistory } from "./MovementHistory";

/**
 * Container: the item detail screen -- stock stepper, physical count, edit
 * and archive. The stepper and the count keep working offline (they go
 * through the outbox); archiving needs the server, so it is disabled
 * offline with an explanation, like creating and editing (T6 decisions).
 */
export function ItemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const itemId = id ?? "";
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();

  const item = useItem(itemId);
  const movements = useMovements(itemId);
  const recordMovement = useRecordMovement();
  const archiveItem = useArchiveItem();

  const [countOpen, setCountOpen] = useState(false);
  const [countText, setCountText] = useState("");
  const [countTouched, setCountTouched] = useState(false);
  const [archiveOpen, setArchiveOpen] = useState(false);

  if (item.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // A failed refetch keeps the cached item in `item.data` (e.g. after a
  // reload offline); only the server saying the item is gone replaces it.
  const isNotFound = item.error instanceof ApiError && item.error.status === 404;
  if (isNotFound || !item.data) {
    const errorCode = item.error instanceof ApiError ? item.error.code : "item_not_found";
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-4 px-4 py-8">
        <Alert variant="error">{getInventoryErrorMessage(errorCode)}</Alert>
        <LinkButton to="/inventario" variant="secondary">
          {inventoryCopy.detail.backToList}
        </LinkButton>
      </main>
    );
  }

  const data = item.data;

  const movementErrorMessage =
    recordMovement.error instanceof ApiError
      ? getInventoryErrorMessage(recordMovement.error.code)
      : undefined;

  const counted = parseStockQuantity(countText);
  const countInvalid = counted === undefined || counted > MAX_STOCK;

  function openCountDialog() {
    setCountText(String(data.stock));
    setCountTouched(false);
    setCountOpen(true);
  }

  function handleCountSubmit() {
    setCountTouched(true);
    // An empty or invalid entry must never become a count of 0: that would
    // silently wipe the real stock. (`counted === undefined` is already part
    // of `countInvalid`; repeated so TypeScript narrows `counted`.)
    if (countInvalid || counted === undefined) {
      return;
    }
    recordMovement.mutate(
      { itemId, kind: "adjust", quantity: counted },
      { onSuccess: () => setCountOpen(false) },
    );
  }

  function handleArchiveConfirm() {
    archiveItem.mutate(itemId, {
      onSuccess: () => navigate("/inventario", { replace: true }),
    });
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 px-4 py-8">
      <header>
        <h1 className="text-2xl font-bold text-brand-primary">{data.name}</h1>
        <p className="text-sm text-brand-muted-foreground">
          {[data.category, data.unit].filter(Boolean).join(" · ")}
        </p>
        {data.sale_price_cents != null ? (
          <p className="mt-1 text-base font-semibold text-brand-foreground">
            {`${inventoryCopy.detail.priceLabel}: ${formatCents(data.sale_price_cents)}`}
          </p>
        ) : null}
      </header>

      {movementErrorMessage ? <Alert variant="error">{movementErrorMessage}</Alert> : null}

      <section className="flex flex-col items-center gap-4 rounded-2xl border border-brand-border bg-brand-card py-8">
        <p className="text-base text-brand-muted-foreground">{inventoryCopy.detail.stockLabel}</p>
        <p className="text-6xl font-bold tabular-nums text-brand-primary">{data.stock}</p>
        <div className="flex gap-4">
          <button
            type="button"
            aria-label={inventoryCopy.list.decrementLabel(data.name)}
            onClick={() => recordMovement.mutate({ itemId, kind: "out", quantity: 1 })}
            className="flex h-14 w-14 items-center justify-center rounded-xl bg-brand-muted text-2xl font-bold text-brand-primary active:bg-brand-border"
          >
            −
          </button>
          <button
            type="button"
            aria-label={inventoryCopy.list.incrementLabel(data.name)}
            onClick={() => recordMovement.mutate({ itemId, kind: "in", quantity: 1 })}
            className="flex h-14 w-14 items-center justify-center rounded-xl bg-brand-accent text-2xl font-bold text-brand-on-accent active:bg-brand-secondary"
          >
            +
          </button>
        </div>
        <Button variant="secondary" onClick={openCountDialog}>
          {inventoryCopy.detail.countAction}
        </Button>
      </section>

      {isOffline ? <Alert variant="info">{inventoryCopy.offline.archiveDisabled}</Alert> : null}

      <div className="flex gap-3">
        <LinkButton to={`/inventario/${itemId}/editar`} variant="secondary" className="flex-1">
          {inventoryCopy.detail.editAction}
        </LinkButton>
        <Button variant="destructive" onClick={() => setArchiveOpen(true)} disabled={isOffline}>
          {inventoryCopy.detail.archiveAction}
        </Button>
      </div>

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-bold text-brand-primary">{inventoryCopy.detail.historyTitle}</h2>
        <MovementHistory movements={movements.data ?? []} />
      </section>

      <Dialog open={countOpen} title={inventoryCopy.detail.countDialogTitle} onClose={() => setCountOpen(false)}>
        <div className="flex flex-col gap-4">
          <TextField
            label={inventoryCopy.detail.countLabel}
            type="number"
            inputMode="numeric"
            min={0}
            max={MAX_STOCK}
            value={countText}
            onChange={(event) => setCountText(event.target.value)}
            onBlur={() => setCountTouched(true)}
            error={countTouched && countInvalid ? inventoryCopy.create.stockRangeInvalid : undefined}
          />
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setCountOpen(false)}>
              {inventoryCopy.detail.countCancel}
            </Button>
            <Button onClick={handleCountSubmit} loading={recordMovement.isPending}>
              {inventoryCopy.detail.countSubmit}
            </Button>
          </div>
        </div>
      </Dialog>

      <Dialog
        open={archiveOpen}
        title={inventoryCopy.detail.archiveConfirmTitle}
        onClose={() => setArchiveOpen(false)}
      >
        <div className="flex flex-col gap-4">
          <p className="text-base text-brand-foreground">{inventoryCopy.detail.archiveConfirmBody}</p>
          {isOffline ? <Alert variant="info">{inventoryCopy.offline.archiveDisabled}</Alert> : null}
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setArchiveOpen(false)}>
              {inventoryCopy.detail.archiveConfirmCancel}
            </Button>
            <Button
              variant="destructive"
              onClick={handleArchiveConfirm}
              loading={archiveItem.isPending}
              disabled={isOffline || archiveItem.isPending}
            >
              {inventoryCopy.detail.archiveConfirmSubmit}
            </Button>
          </div>
        </div>
      </Dialog>
    </main>
  );
}

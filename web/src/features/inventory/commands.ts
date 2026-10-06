import { flushOutboxOnce, notifyOutboxChange, waitForOutcome } from "./offlineSync";
import { defaultOutbox, type Outbox, type OutboxEntry } from "./outbox";
import type { ItemOut, ItemStockSummary, MovementKind, MovementOut } from "./api";

export interface RecordMovementInput {
  itemId: string;
  kind: MovementKind;
  quantity: number;
  note?: string;
}

export interface RecordMovementContext {
  workshopId: string;
  outbox?: Outbox;
}

/** The server accepted and applied this movement while we waited. */
export interface RecordMovementSynced {
  status: "synced";
  movement: MovementOut;
  item: ItemStockSummary;
}

/** The movement is durably queued; it will be sent once the outbox flushes. */
export interface RecordMovementQueued {
  status: "queued";
}

export type RecordMovementResult = RecordMovementSynced | RecordMovementQueued;

/**
 * The single place every stock change goes through, for the list, the
 * detail stepper and the physical count dialog alike. It generates the
 * movement's id and `occurred_at` on the client so a retried or replayed
 * call is idempotent (see the T3 ledger), then durably queues the movement
 * in the offline outbox *before* attempting to send it.
 *
 * Sending always goes through `flushOutboxOnce`, the same single FIFO
 * flush pipeline used for background sync (app start, the `online` event,
 * the periodic timer). Two rapid taps therefore never race as independent
 * parallel PUTs -- the second tap's movement is never sent to the server
 * until the first's request has fully settled -- so a cache reconciliation
 * can never apply a stale response after a newer one.
 */
export async function recordMovement(
  input: RecordMovementInput,
  context: RecordMovementContext,
): Promise<RecordMovementResult> {
  const outbox = context.outbox ?? defaultOutbox;
  const movementId = crypto.randomUUID();
  const occurredAt = new Date().toISOString();

  // Registered before the entry exists anywhere else, so no concurrent
  // flush pass (triggered by another recordMovement call, the online
  // event, or the periodic timer) can resolve this id before we're
  // listening for it.
  const outcome = waitForOutcome(movementId);

  await outbox.add({
    id: movementId,
    workshopId: context.workshopId,
    itemId: input.itemId,
    kind: input.kind,
    quantity: input.quantity,
    note: input.note,
    occurredAt,
  });
  notifyOutboxChange();

  const flushed = flushOutboxOnce({ outbox, workshopId: context.workshopId }).then(() => "flushed" as const);

  const settled = await Promise.race([
    outcome.then((value) => ({ kind: "outcome" as const, value })),
    flushed.then(() => ({ kind: "flushed" as const })),
  ]);

  if (settled.kind === "outcome") {
    if (settled.value.kind === "sent") {
      return { status: "synced", movement: settled.value.movement, item: settled.value.item };
    }
    throw settled.value.error;
  }

  // Our own triggered pass (or whichever pass ran first) finished without
  // resolving this entry's outcome: it is still offline/queued.
  return { status: "queued" };
}

/**
 * Applies a movement to an item's cached stock fields optimistically, with
 * the same rules the API uses: `in`/`out` move the stock by `quantity`, an
 * `adjust` replaces it with the counted `quantity`; `needs_review` and
 * `is_low` are re-derived from the resulting stock.
 */
export function applyMovementToItem(
  item: ItemOut,
  input: Pick<RecordMovementInput, "kind" | "quantity">,
): ItemOut {
  const stock =
    input.kind === "adjust"
      ? input.quantity
      : item.stock + (input.kind === "in" ? input.quantity : -input.quantity);

  return {
    ...item,
    stock,
    needs_review: stock < 0,
    is_low: item.min_stock > 0 && stock <= item.min_stock,
  };
}

/**
 * Folds every still-queued outbox entry for `item.id` on top of `item`, in
 * FIFO order. Used by `useItem`/`useItems` so that an item's displayed
 * stock keeps reflecting a movement that is queued-but-not-yet-synced even
 * after a reload or a server refetch that resolves before the outbox has
 * had a chance to flush (see T6 decisions: this is the chosen alternative
 * to relying solely on the persisted optimistic cache).
 */
export function applyPendingOutboxEntries(item: ItemOut, pending: OutboxEntry[]): ItemOut {
  const relevant = pending.filter((entry) => entry.itemId === item.id).sort((a, b) => a.seq - b.seq);
  return relevant.reduce((current, entry) => applyMovementToItem(current, entry), item);
}

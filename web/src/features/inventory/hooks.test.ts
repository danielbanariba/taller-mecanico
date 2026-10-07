import { describe, expect, it } from "vitest";

import type { ItemOut, MovementResult } from "./api";
import { fetchItemFolded } from "./hooks";
import { flushOutboxOnce } from "./offlineSync";
import type { Outbox, OutboxEntry } from "./outbox";

function createDeferred<T = void>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

const BASE_ITEM: ItemOut = {
  id: "item-1",
  name: "Filtro de aceite",
  category: null,
  unit: "unidad",
  min_stock: 0,
  sale_price_cents: null,
  notes: null,
  stock: 10,
  needs_review: false,
  is_low: false,
  archived_at: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

/**
 * An in-memory outbox whose remove() can be held open by the test, so the
 * test can reproduce the exact window a flush pass spends between a
 * successful PUT and actually removing the entry, without racing real
 * IndexedDB or network timing.
 */
function createGatedOutbox(initial: OutboxEntry[]) {
  let records = [...initial];
  const removeGate = createDeferred<void>();

  const outbox: Outbox = {
    async add(entry) {
      const stored: OutboxEntry = { ...entry, attempts: 0, seq: records.length + 1 };
      records = [...records, stored];
      return stored;
    },
    async remove(id) {
      await removeGate.promise;
      records = records.filter((record) => record.id !== id);
    },
    async recordFailure(id, code) {
      records = records.map((record) =>
        record.id === id ? { ...record, attempts: record.attempts + 1, lastError: code } : record,
      );
    },
    async list() {
      return [...records].sort((a, b) => a.seq - b.seq);
    },
    async listForWorkshop(workshopId) {
      return (await outbox.list()).filter((record) => record.workshopId === workshopId);
    },
  };

  return { outbox, openRemoveGate: removeGate.resolve };
}

/** Lets every currently-queued microtask run before the next line executes. */
function flushMicrotasks(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

describe("fetchItemFolded", () => {
  it("never double-counts a movement when a read lands between a flush's successful PUT and its outbox removal", async () => {
    // Defect this catches: useItem's queryFn fetched the server item and
    // read the outbox without any synchronization with the flush pass, so
    // a refetch landing after the server applied a movement but before
    // flushOutboxOnce removed its outbox entry folded that movement a
    // second time onto server data that already included it, inflating
    // the shown stock until the next fetch.
    const workshopId = "workshop-1";
    const pendingEntry: OutboxEntry = {
      id: "queued-in",
      workshopId,
      itemId: "item-1",
      kind: "in",
      quantity: 1,
      occurredAt: "2026-01-01T00:05:00.000Z",
      attempts: 0,
      seq: 1,
    };
    const { outbox, openRemoveGate } = createGatedOutbox([pendingEntry]);

    let serverStock = 10;
    const putCalled = createDeferred<void>();
    const putMovement = async (): Promise<MovementResult> => {
      serverStock = 11; // the server applies the queued movement...
      putCalled.resolve();
      return {
        movement: {
          id: "queued-in",
          item_id: "item-1",
          kind: "in",
          quantity: 1,
          delta: 1,
          note: null,
          occurred_at: "2026-01-01T00:05:00.000Z",
          recorded_at: "2026-01-01T00:05:01.000Z",
          created_by: "u1",
        },
        item: { id: "item-1", stock: serverStock, needs_review: false, is_low: false },
      };
    };
    // ...but the entry is still queued: remove() is gated and hasn't run yet.
    const getItem = async () => ({ ...BASE_ITEM, stock: serverStock });

    const flushPromise = flushOutboxOnce({ outbox, workshopId, putMovement });
    await putCalled.promise;

    const readPromise = fetchItemFolded("item-1", workshopId, { outbox, getItem });

    // Give the read every chance to run to completion on its own (it would,
    // unguarded, since nothing here depends on removeGate yet).
    await flushMicrotasks();

    openRemoveGate();
    const [item] = await Promise.all([readPromise, flushPromise]);

    expect(item.stock).toBe(11);
  });
});

import { createStore } from "idb-keyval";
import { http, HttpResponse, delay } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/server";
import { createOutbox, type NewOutboxEntry } from "./outbox";
import { flushOutboxOnce } from "./offlineSync";

let dbCounter = 0;

function freshOutbox() {
  dbCounter += 1;
  return createOutbox(createStore(`taller-offline-sync-test-${dbCounter}`, "movements"));
}

function entry(overrides: Partial<NewOutboxEntry> = {}): NewOutboxEntry {
  return {
    id: overrides.id ?? "movement-1",
    workshopId: overrides.workshopId ?? "workshop-1",
    itemId: overrides.itemId ?? "item-1",
    kind: overrides.kind ?? "in",
    quantity: overrides.quantity ?? 1,
    occurredAt: overrides.occurredAt ?? "2026-01-01T00:00:00.000Z",
  };
}

function movementResponse(stock: number) {
  return {
    movement: {
      id: "server-id",
      item_id: "item-1",
      kind: "in",
      quantity: 1,
      delta: 1,
      note: null,
      occurred_at: "2026-01-01T00:00:00.000Z",
      recorded_at: "2026-01-01T00:00:00.000Z",
      created_by: "user-1",
    },
    item: { id: "item-1", stock, needs_review: false, is_low: false },
  };
}

describe("flushOutboxOnce", () => {
  it("sends queued entries in FIFO order and removes each on a 201", async () => {
    // Defect this catches: sending entries out of insertion order (or in
    // parallel) can apply an "adjust" before an earlier "in"/"out" for the
    // same item, corrupting the final stock.
    const outbox = freshOutbox();
    await outbox.add(entry({ id: "first" }));
    await outbox.add(entry({ id: "second" }));

    const receivedOrder: string[] = [];
    server.use(
      http.put("/api/inventory/movements/:id", ({ params }) => {
        receivedOrder.push(params.id as string);
        return HttpResponse.json(movementResponse(10), { status: 201 });
      }),
    );

    const result = await flushOutboxOnce({ outbox, workshopId: "workshop-1" });

    expect(receivedOrder).toEqual(["first", "second"]);
    expect(result.sent.map((item) => item.id)).toEqual(["first", "second"]);
    expect(await outbox.list()).toHaveLength(0);
  });

  it("keeps the entry queued and stops the pass when the PUT fails with network_error", async () => {
    // Defect this catches: dropping a movement because the phone briefly
    // lost signal would silently lose a mechanic's stock change.
    const outbox = freshOutbox();
    await outbox.add(entry({ id: "stuck" }));
    await outbox.add(entry({ id: "behind-it" }));

    server.use(http.put("/api/inventory/movements/:id", () => HttpResponse.error()));

    const result = await flushOutboxOnce({ outbox, workshopId: "workshop-1" });

    expect(result.sent).toHaveLength(0);
    const remaining = await outbox.list();
    expect(remaining.map((item) => item.id)).toEqual(["stuck", "behind-it"]);
    expect(remaining[0]?.attempts).toBe(1);
    // The pass stops at the first still-offline entry instead of reordering
    // around it, so the one behind it is untouched.
    expect(remaining[1]?.attempts).toBe(0);
  });

  it("removes the entry and reports the error on a definitive 404 rejection, then continues to the next entry", async () => {
    // Defect this catches: an outbox entry for an item that was deleted on
    // another device would otherwise retry forever, blocking every
    // movement queued behind it.
    const outbox = freshOutbox();
    await outbox.add(entry({ id: "missing-item" }));
    await outbox.add(entry({ id: "fine" }));

    server.use(
      http.put("/api/inventory/movements/:id", ({ params }) => {
        if (params.id === "missing-item") {
          return HttpResponse.json({ detail: "item_not_found" }, { status: 404 });
        }
        return HttpResponse.json(movementResponse(5), { status: 201 });
      }),
    );

    const result = await flushOutboxOnce({ outbox, workshopId: "workshop-1" });

    expect(result.removedWithError).toHaveLength(1);
    expect(result.removedWithError[0]?.entry.id).toBe("missing-item");
    expect(result.removedWithError[0]?.error.code).toBe("item_not_found");
    expect(result.sent.map((item) => item.id)).toEqual(["fine"]);
    expect(await outbox.list()).toHaveLength(0);
  });

  it("never sends an entry recorded under a different workshop", async () => {
    // Defect this catches: a different account logging in on the same
    // phone must never flush the previous account's queued movements.
    const outbox = freshOutbox();
    await outbox.add(entry({ id: "other-workshop", workshopId: "workshop-b" }));

    let putCalled = false;
    server.use(
      http.put("/api/inventory/movements/:id", () => {
        putCalled = true;
        return HttpResponse.json(movementResponse(1), { status: 201 });
      }),
    );

    const result = await flushOutboxOnce({ outbox, workshopId: "workshop-a" });

    expect(putCalled).toBe(false);
    expect(result.sent).toHaveLength(0);
    expect(await outbox.list()).toHaveLength(1);
  });

  it("never has two PUTs in flight at once, even when two flush calls overlap", async () => {
    // Defect this catches: concurrent flush passes could send two
    // movements for the same item in parallel, letting a fast second
    // response be overwritten by a slow first one that arrives later.
    const outbox = freshOutbox();
    await outbox.add(entry({ id: "a" }));
    await outbox.add(entry({ id: "b" }));

    let inFlight = 0;
    let maxInFlight = 0;
    server.use(
      http.put("/api/inventory/movements/:id", async () => {
        inFlight += 1;
        maxInFlight = Math.max(maxInFlight, inFlight);
        await delay(20);
        inFlight -= 1;
        return HttpResponse.json(movementResponse(2), { status: 201 });
      }),
    );

    await Promise.all([
      flushOutboxOnce({ outbox, workshopId: "workshop-1" }),
      flushOutboxOnce({ outbox, workshopId: "workshop-1" }),
    ]);

    expect(maxInFlight).toBe(1);
    expect(await outbox.list()).toHaveLength(0);
  });
});

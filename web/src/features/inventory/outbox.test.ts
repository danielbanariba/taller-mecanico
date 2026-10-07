import { createStore } from "idb-keyval";
import { describe, expect, it } from "vitest";

import { createOutbox } from "./outbox";

let dbCounter = 0;

/** A fresh, isolated IndexedDB store per test so outbox tests never see each other's entries. */
function freshStore() {
  dbCounter += 1;
  return createStore(`taller-outbox-test-${dbCounter}`, "movements");
}

function entry(overrides: Partial<Parameters<ReturnType<typeof createOutbox>["add"]>[0]> = {}) {
  return {
    id: overrides.id ?? "movement-1",
    workshopId: overrides.workshopId ?? "workshop-1",
    itemId: overrides.itemId ?? "item-1",
    kind: overrides.kind ?? ("in" as const),
    quantity: overrides.quantity ?? 1,
    occurredAt: overrides.occurredAt ?? "2026-01-01T00:00:00.000Z",
    note: overrides.note,
  };
}

describe("outbox", () => {
  it("survives a reload: a new outbox instance over the same store still sees a previously added entry", async () => {
    // Defect this catches: an outbox that only keeps entries in memory would
    // lose every queued movement the moment the app (or the test process)
    // restarts, defeating the entire point of an offline queue.
    const store = freshStore();
    const outbox = createOutbox(store);
    await outbox.add(entry({ id: "m1" }));

    const reloaded = createOutbox(store);
    const entries = await reloaded.list();

    expect(entries).toHaveLength(1);
    expect(entries[0]?.id).toBe("m1");
    expect(entries[0]?.attempts).toBe(0);
  });

  it("list() returns entries in FIFO insertion order regardless of id ordering", async () => {
    // Defect this catches: ordering by id or by object-store iteration order
    // (neither of which tracks insertion time) could replay an "adjust"
    // movement before an earlier "in"/"out" for the same item, corrupting
    // the resulting stock.
    const outbox = createOutbox(freshStore());
    await outbox.add(entry({ id: "z-last" }));
    await outbox.add(entry({ id: "a-first" }));
    await outbox.add(entry({ id: "m-middle" }));

    const entries = await outbox.list();

    expect(entries.map((item) => item.id)).toEqual(["z-last", "a-first", "m-middle"]);
  });

  it("remove() deletes the entry so it no longer appears in list()", async () => {
    const outbox = createOutbox(freshStore());
    await outbox.add(entry({ id: "m1" }));
    await outbox.add(entry({ id: "m2" }));

    await outbox.remove("m1");

    expect((await outbox.list()).map((item) => item.id)).toEqual(["m2"]);
  });

  it("recordFailure() increments attempts and keeps the entry queued", async () => {
    // Defect this catches: if a failed send silently dropped the entry (or
    // never recorded the attempt), the UI banner would have no way to know
    // a movement has been retried and is still stuck.
    const outbox = createOutbox(freshStore());
    await outbox.add(entry({ id: "m1" }));

    await outbox.recordFailure("m1", "network_error");
    await outbox.recordFailure("m1", "network_error");

    const [stored] = await outbox.list();
    expect(stored?.attempts).toBe(2);
    expect(stored?.lastError).toBe("network_error");
  });

  it("listForWorkshop() excludes entries recorded under a different workshop", async () => {
    // Defect this catches: a second account logging in on the same phone
    // must never have another workshop's queued movements sent under its
    // session.
    const outbox = createOutbox(freshStore());
    await outbox.add(entry({ id: "mine", workshopId: "workshop-a" }));
    await outbox.add(entry({ id: "not-mine", workshopId: "workshop-b" }));

    const entries = await outbox.listForWorkshop("workshop-a");

    expect(entries.map((item) => item.id)).toEqual(["mine"]);
  });

  it("assigns distinct, increasing sequence numbers to concurrent add() calls, preserving call order", async () => {
    // Defect this catches: nextSeq() computed `max(seq) + 1` as a read
    // separate from add()'s write, so two concurrent add() calls (e.g. two
    // browser tabs) could both read the same max and be assigned the same
    // seq, losing FIFO determinism between them.
    const outbox = createOutbox(freshStore());

    const [a, b, c] = await Promise.all([
      outbox.add(entry({ id: "a" })),
      outbox.add(entry({ id: "b" })),
      outbox.add(entry({ id: "c" })),
    ]);

    expect([a.seq, b.seq, c.seq]).toEqual([1, 2, 3]);
    expect((await outbox.list()).map((item) => item.id)).toEqual(["a", "b", "c"]);
  });
});

import { createStore } from "idb-keyval";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/server";
import { recordMovement } from "./commands";
import { createOutbox } from "./outbox";

let dbCounter = 0;

function freshOutbox() {
  dbCounter += 1;
  return createOutbox(createStore(`taller-commands-test-${dbCounter}`, "movements"));
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

describe("recordMovement", () => {
  it("returns queued and leaves the entry in the outbox when the network is down", async () => {
    // Defect this catches: if recordMovement swallowed a network failure
    // without queuing anything, an offline stock change would be lost
    // instead of synced once the connection returns.
    const outbox = freshOutbox();
    server.use(http.put("/api/inventory/movements/:id", () => HttpResponse.error()));

    const result = await recordMovement(
      { itemId: "item-1", kind: "in", quantity: 1 },
      { workshopId: "workshop-1", outbox },
    );

    expect(result).toEqual({ status: "queued" });
    expect(await outbox.listForWorkshop("workshop-1")).toHaveLength(1);
  });

  it("returns synced with the server's movement and item when the PUT succeeds", async () => {
    const outbox = freshOutbox();
    server.use(http.put("/api/inventory/movements/:id", () => HttpResponse.json(movementResponse(11), { status: 201 })));

    const result = await recordMovement(
      { itemId: "item-1", kind: "in", quantity: 1 },
      { workshopId: "workshop-1", outbox },
    );

    expect(result.status).toBe("synced");
    if (result.status === "synced") {
      expect(result.item.stock).toBe(11);
    }
    expect(await outbox.listForWorkshop("workshop-1")).toHaveLength(0);
  });

  it("removes the entry and throws the ApiError on a definitive rejection", async () => {
    // Defect this catches: keeping a movement for a deleted item queued
    // forever would block every later movement behind it in the outbox.
    const outbox = freshOutbox();
    server.use(
      http.put("/api/inventory/movements/:id", () => HttpResponse.json({ detail: "item_not_found" }, { status: 404 })),
    );

    await expect(
      recordMovement({ itemId: "item-1", kind: "in", quantity: 1 }, { workshopId: "workshop-1", outbox }),
    ).rejects.toMatchObject({ code: "item_not_found" });
    expect(await outbox.listForWorkshop("workshop-1")).toHaveLength(0);
  });

  it("sends two rapid movements for the same workshop to the server strictly one at a time, in call order", async () => {
    // Defect this catches: issuing each recordMovement call as its own
    // independent, unsynchronized PUT lets a fast second response and a
    // slow first response be applied to the cache in the wrong order (see
    // the out-of-order reconciliation bug found in the T5 review). Routing
    // every send through the single FIFO flush means the server never has
    // two of this workshop's movement PUTs in flight at once.
    const outbox = freshOutbox();
    const receivedOrder: string[] = [];
    let inFlight = 0;
    let maxInFlight = 0;

    server.use(
      http.put("/api/inventory/movements/:id", async ({ params }) => {
        inFlight += 1;
        maxInFlight = Math.max(maxInFlight, inFlight);
        receivedOrder.push(params.id as string);
        await new Promise((resolve) => setTimeout(resolve, 10));
        inFlight -= 1;
        return HttpResponse.json(movementResponse(2), { status: 201 });
      }),
    );

    const first = recordMovement({ itemId: "item-1", kind: "in", quantity: 1 }, { workshopId: "workshop-1", outbox });
    const second = recordMovement({ itemId: "item-1", kind: "in", quantity: 1 }, { workshopId: "workshop-1", outbox });

    await Promise.all([first, second]);

    expect(maxInFlight).toBe(1);
    expect(receivedOrder).toHaveLength(2);
  });
});

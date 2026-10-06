import type { ReactNode } from "react";
import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../../test/server";
import { useOfflineSync } from "./hooks";
import { defaultOutbox } from "./outbox";

const WORKSHOP_ID = "workshop-online-test";

function renderOfflineSync() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return renderHook(() => useOfflineSync(WORKSHOP_ID), {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  });
}

describe("useOfflineSync", () => {
  it("sends a queued movement exactly once when the browser's online event fires", async () => {
    // Defect this catches: without an `online` listener, a movement queued
    // while offline would only reach the server on the next full reload or
    // after waiting out the 30s periodic timer, instead of as soon as the
    // connection actually returns.
    await defaultOutbox.add({
      id: "online-event-movement",
      workshopId: WORKSHOP_ID,
      itemId: "item-1",
      kind: "in",
      quantity: 1,
      occurredAt: "2026-01-01T00:00:00.000Z",
    });

    // Offline on mount: the hook's own mount-triggered flush attempt fails
    // and leaves the entry queued, so the assertions below are about the
    // `online` event specifically, not the mount flush.
    server.use(http.put("/api/inventory/movements/:id", () => HttpResponse.error()));

    renderOfflineSync();
    await waitFor(async () => {
      expect(await defaultOutbox.listForWorkshop(WORKSHOP_ID)).toHaveLength(1);
    });

    let putCount = 0;
    server.use(
      http.put("/api/inventory/movements/:id", () => {
        putCount += 1;
        return HttpResponse.json(
          {
            movement: {
              id: "online-event-movement",
              item_id: "item-1",
              kind: "in",
              quantity: 1,
              delta: 1,
              note: null,
              occurred_at: "2026-01-01T00:00:00.000Z",
              recorded_at: "2026-01-01T00:00:00.000Z",
              created_by: "u1",
            },
            item: { id: "item-1", stock: 1, needs_review: false, is_low: false },
          },
          { status: 201 },
        );
      }),
    );

    act(() => {
      window.dispatchEvent(new Event("online"));
    });

    await waitFor(() => expect(putCount).toBe(1));
    await waitFor(async () => {
      expect(await defaultOutbox.listForWorkshop(WORKSHOP_ID)).toHaveLength(0);
    });
  });

  it("reports the pending count for the current workshop", async () => {
    const workshopId = "workshop-pending-count";
    await defaultOutbox.add({
      id: "pending-count-movement",
      workshopId,
      itemId: "item-1",
      kind: "in",
      quantity: 1,
      occurredAt: "2026-01-01T00:00:00.000Z",
    });
    server.use(http.put("/api/inventory/movements/:id", () => HttpResponse.error()));

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { result } = renderHook(() => useOfflineSync(workshopId), {
      wrapper: ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      ),
    });

    await waitFor(() => expect(result.current.pendingCount).toBe(1));
  });
});

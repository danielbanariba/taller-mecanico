import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";

import { sessionQueryKey } from "../auth/hooks";
import { inventoryQueryKey } from "../inventory/hooks";
import { server } from "../../test/server";
import { statusActionLabel, workOrdersCopy } from "./copy";
import { StatusActions } from "./StatusActions";
import type { WorkOrderOut, WorkOrderStatus } from "./api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

function order(overrides: Partial<WorkOrderOut> = {}): WorkOrderOut {
  return {
    id: "order-1",
    number: 42,
    status: "approved",
    allowed_transitions: ["in_progress", "cancelled"],
    lines_editable: true,
    active_invoice: null,
    vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
    customer: { id: "c1", full_name: "María Hernández", phone: "98765432", phone_is_mobile: true },
    complaint: null,
    odometer_km: null,
    notes: null,
    lines: [],
    total_cents: 0,
    payments: [],
    paid_cents: 0,
    balance_cents: 0,
    accepts_payments: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    approved_at: null,
    started_at: null,
    completed_at: null,
    delivered_at: null,
    cancelled_at: null,
    ...overrides,
  };
}

function mockSession() {
  server.use(http.get("/api/auth/me", () => HttpResponse.json(SESSION)));
}

/** Pre-populates the session so `useChangeStatus`'s `useWorkshopId()` resolves to "w1" on the very first render, with no race against the background refetch `mockSession()` still answers. */
function renderStatusActions(orderData: WorkOrderOut, client?: QueryClient) {
  const queryClient = client ?? new QueryClient({ defaultOptions: { queries: { retry: false } } });
  queryClient.setQueryData(sessionQueryKey, SESSION);
  const utils = render(
    <QueryClientProvider client={queryClient}>
      <StatusActions order={orderData} />
    </QueryClientProvider>,
  );
  return { queryClient, ...utils };
}

describe("StatusActions", () => {
  it("renders exactly the buttons the server allows, never a hard-coded transition table", () => {
    // Defect this catches: a client-side transition table drifting from
    // the server's own state machine (`design.md`'s AD-7) -- this order
    // is given an unusual pair (`quote`, `delivered`) that no real
    // status ever allows together, so passing here only works if the
    // buttons are read from `allowed_transitions` and nothing else.
    mockSession();
    renderStatusActions(
      order({ status: "in_progress", allowed_transitions: ["quote", "delivered"] as WorkOrderStatus[] }),
    );

    expect(screen.getByRole("button", { name: statusActionLabel("quote") })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: statusActionLabel("delivered") })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: statusActionLabel("cancelled") })).not.toBeInTheDocument();
    expect(screen.getAllByRole("button")).toHaveLength(2);
  });

  it("invalidates inventory queries after a successful status change, so stock refetches", async () => {
    // Defect this catches: the inventory list/detail screens showing
    // stale stock after "Iniciar trabajo" consumes it server-side,
    // because only the work-order queries were invalidated and nothing
    // told the inventory screens their cached data was now wrong.
    mockSession();
    server.use(
      http.put("/api/work-orders/order-1/status", () =>
        HttpResponse.json(order({ status: "in_progress", allowed_transitions: ["completed", "cancelled"] })),
      ),
    );
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
    const user = userEvent.setup();
    renderStatusActions(order(), queryClient);

    await user.click(screen.getByRole("button", { name: statusActionLabel("in_progress") }));

    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: inventoryQueryKey("w1") }),
      );
    });
  });

  it("requires confirmation before cancelling, and confirming sends exactly one cancel request", async () => {
    // Defect this catches: a single accidental tap on "Cancelar orden"
    // irreversibly cancelling an in-progress order and reversing its
    // already-consumed stock, with no chance to back out.
    mockSession();
    let cancelRequests = 0;
    server.use(
      http.put("/api/work-orders/order-1/status", async ({ request }) => {
        cancelRequests += 1;
        await expect(request.json()).resolves.toEqual({ status: "cancelled" });
        return HttpResponse.json(order({ status: "cancelled", allowed_transitions: [] }));
      }),
    );
    const user = userEvent.setup();
    renderStatusActions(order({ status: "in_progress", allowed_transitions: ["completed", "cancelled"] }));

    await user.click(screen.getByRole("button", { name: statusActionLabel("cancelled") }));
    expect(cancelRequests).toBe(0);
    expect(screen.getByText(workOrdersCopy.cancelConfirm.bodyInProgress)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: workOrdersCopy.cancelConfirm.confirm }));

    await waitFor(() => {
      expect(cancelRequests).toBe(1);
    });
  });

  it("sends nothing and leaves the order unchanged when the cancellation is dismissed", async () => {
    // Defect this catches: dismissing the confirmation still cancelling
    // the order, or the dialog leaking a request after it closes.
    mockSession();
    let cancelRequests = 0;
    server.use(
      http.put("/api/work-orders/order-1/status", () => {
        cancelRequests += 1;
        return HttpResponse.json(order({ status: "cancelled", allowed_transitions: [] }));
      }),
    );
    const user = userEvent.setup();
    renderStatusActions(order());

    await user.click(screen.getByRole("button", { name: statusActionLabel("cancelled") }));
    await user.click(screen.getByRole("button", { name: workOrdersCopy.cancelConfirm.keep }));

    expect(screen.queryByText(workOrdersCopy.cancelConfirm.body)).not.toBeInTheDocument();
    expect(cancelRequests).toBe(0);
    expect(screen.getByRole("button", { name: statusActionLabel("in_progress") })).toBeInTheDocument();
  });

  it("maps a 409 work_order_has_payments to its own Spanish message, not the generic fallback", async () => {
    // Defect this catches: the cancel guard's `work_order_has_payments`
    // 409 (the `payments` spec's "Cancelling An Order Counts Only Its
    // Non-Voided Payments") had no entry in `copy.ts`'s `ERROR_MESSAGES`,
    // so a mechanic saw "Ocurrió un error. Intente de nuevo." with no way
    // to understand that an unvoided payment is blocking cancellation.
    mockSession();
    server.use(
      http.put("/api/work-orders/order-1/status", () =>
        HttpResponse.json({ detail: "work_order_has_payments" }, { status: 409 }),
      ),
    );
    const user = userEvent.setup();
    renderStatusActions(order({ status: "in_progress", allowed_transitions: ["completed", "cancelled"] }));

    await user.click(screen.getByRole("button", { name: statusActionLabel("cancelled") }));
    await user.click(screen.getByRole("button", { name: workOrdersCopy.cancelConfirm.confirm }));

    expect(
      await screen.findByText("No se puede cancelar una orden con pagos registrados. Anule los pagos primero."),
    ).toBeInTheDocument();
  });

  it("disables every status button offline, with the Spanish explanation", () => {
    // Defect this catches: an offline tap reaching the API -- AD-17's
    // write-requires-connection rule, which every other mutation in this
    // feature already follows, and which status changes must not skip.
    //
    // Runs last on purpose: `navigator.onLine` is an inherited jsdom
    // prototype property, so this override outlives the test (mirrors
    // `NewWorkOrderPage.test.tsx`'s own note).
    mockSession();
    Object.defineProperty(window.navigator, "onLine", { value: false, configurable: true });
    renderStatusActions(order());

    expect(screen.getByText(workOrdersCopy.offline.statusChangeDisabled)).toBeInTheDocument();
    for (const button of screen.getAllByRole("button")) {
      expect(button).toBeDisabled();
    }
  });
});

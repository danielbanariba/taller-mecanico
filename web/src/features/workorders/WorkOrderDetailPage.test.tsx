import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { sessionQueryKey } from "../auth/hooks";
import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { workOrderQueryKey } from "./hooks";
import { WorkOrderDetailPage } from "./WorkOrderDetailPage";
import type { WorkOrderOut } from "./api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

const ORDER: WorkOrderOut = {
  id: "order-1",
  number: 42,
  status: "quote",
  allowed_transitions: ["approved", "cancelled"],
  lines_editable: true,
  vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
  customer: { id: "c1", full_name: "María Hernández", phone: "98765432", phone_is_mobile: true },
  complaint: "Ruido en motor",
  odometer_km: 45000,
  notes: null,
  lines: [
    {
      id: "line-1",
      kind: "labor",
      item_id: null,
      description: "Cambio de aceite",
      quantity: 1,
      unit_price_cents: 50000,
      line_total_cents: 50000,
      stock_posted_quantity: 0,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  ],
  total_cents: 50000,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  approved_at: null,
  started_at: null,
  completed_at: null,
  delivered_at: null,
  cancelled_at: null,
};

function mockSessionAndOrder() {
  server.use(
    http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
    http.get("/api/work-orders/order-1", () => HttpResponse.json(ORDER)),
  );
}

function renderDetailPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/ordenes/order-1"]}>
      <Routes>
        <Route path="/ordenes/:orderId" element={<WorkOrderDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

/**
 * Renders the page over a cache that already holds the session and the
 * order -- what the persister restores from IndexedDB -- while every
 * request fails as it does without a connection.
 */
function renderDetailPageFromCacheWithoutConnection() {
  server.use(
    http.get("/api/auth/me", () => HttpResponse.error()),
    http.get("/api/work-orders/order-1", () => HttpResponse.error()),
  );
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  queryClient.setQueryData(sessionQueryKey, SESSION);
  queryClient.setQueryData(workOrderQueryKey("w1", "order-1"), ORDER);

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/ordenes/order-1"]}>
        <Routes>
          <Route path="/ordenes/:orderId" element={<WorkOrderDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("WorkOrderDetailPage", () => {
  it("renders the order's number, vehicle, lines and total, with no status actions yet", async () => {
    // Defect this catches: the read-only detail screen failing to render
    // the order it just fetched, or a line's price/total mis-mapped
    // from WorkOrderLineOut. No status button exists yet in this slice
    // (S6 wires them from `allowed_transitions`), so none is asserted.
    mockSessionAndOrder();
    renderDetailPage();

    expect(await screen.findByRole("heading", { name: "Orden #42" })).toBeInTheDocument();
    expect(screen.getByText("Cambio de aceite")).toBeInTheDocument();
    expect(screen.getByText("María Hernández")).toBeInTheDocument();
    expect(screen.getByText("Total").closest("p")).toHaveTextContent("L 500.00");
  });

  it("keeps showing the cached order when refetching it fails for lack of connection", async () => {
    // Defect this catches: a failed refetch flips the order query to
    // "error" while it still holds the cached order; checking the
    // not-found branch before the cached data would make a previously
    // visited order disappear the moment the device goes offline.
    renderDetailPageFromCacheWithoutConnection();

    expect(await screen.findByRole("heading", { name: "Orden #42" })).toBeInTheDocument();
    expect(screen.queryByText("No se encontró la orden.")).not.toBeInTheDocument();
  });
});

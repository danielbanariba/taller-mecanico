import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { server } from "../../../test/server";
import { ReceiptLetterPage } from "./ReceiptLetterPage";
import type { WorkOrderOut } from "../api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

const ORDER: WorkOrderOut = {
  id: "order-1",
  number: 42,
  status: "delivered",
  allowed_transitions: [],
  lines_editable: false,
  vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
  customer: { id: "c1", full_name: "María Hernández", phone: "98765432", phone_is_mobile: true },
  complaint: null,
  odometer_km: null,
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
  payments: [],
  paid_cents: 50000,
  balance_cents: 0,
  accepts_payments: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  approved_at: null,
  started_at: null,
  completed_at: null,
  delivered_at: "2026-01-03T00:00:00Z",
  cancelled_at: null,
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/ordenes/order-1/recibo/carta"]}>
        <Routes>
          <Route path="/ordenes/:orderId/recibo/carta" element={<ReceiptLetterPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ReceiptLetterPage", () => {
  it("renders a delivered order's content with a margin-only @page rule, so Letter and A4 both work", async () => {
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/work-orders/order-1", () => HttpResponse.json(ORDER)),
    );
    const { container } = renderPage();
    expect(await screen.findByText("Orden #42")).toBeInTheDocument();
    const styleTag = container.querySelector("style");
    expect(styleTag?.textContent).toContain("margin: 12mm");
    // Unlike the 58mm layout, this layout must never pin a `size` -- that
    // would override the browser's own Letter/A4 default (AD-19).
    expect(styleTag?.textContent).not.toContain("size:");
  });

  it("does not render order data for an order that is not completed or delivered, and explains why", async () => {
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/work-orders/order-1", () => HttpResponse.json({ ...ORDER, status: "in_progress" })),
    );
    renderPage();
    expect(await screen.findByText(/solo está disponible una vez/)).toBeInTheDocument();
    expect(screen.queryByText("Orden #42")).not.toBeInTheDocument();
  });

  it("renders not-found for another workshop's order, with no order data leaked", async () => {
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/work-orders/order-1", () => HttpResponse.json({ detail: "work_order_not_found" }, { status: 404 })),
    );
    renderPage();
    expect(await screen.findByText("No se encontró la orden.")).toBeInTheDocument();
    expect(screen.queryByText("Orden #42")).not.toBeInTheDocument();
  });
});

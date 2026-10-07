import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { server } from "../../../test/server";
import { Receipt58Page } from "./Receipt58Page";
import type { WorkOrderOut } from "../api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

const ORDER: WorkOrderOut = {
  id: "order-1",
  number: 42,
  status: "completed",
  allowed_transitions: ["delivered"],
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
  completed_at: "2026-01-02T00:00:00Z",
  delivered_at: null,
  cancelled_at: null,
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/ordenes/order-1/recibo/58mm"]}>
        <Routes>
          <Route path="/ordenes/:orderId/recibo/58mm" element={<Receipt58Page />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Receipt58Page", () => {
  it("renders a completed order's content, including the non-fiscal label", async () => {
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/work-orders/order-1", () => HttpResponse.json(ORDER)),
    );
    renderPage();
    expect(await screen.findByText("Orden #42")).toBeInTheDocument();
    expect(screen.getAllByText("DOCUMENTO NO FISCAL — No válido como factura").length).toBeGreaterThan(0);
  });

  it("does not render order data for an order that is not completed or delivered, and explains why", async () => {
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/work-orders/order-1", () => HttpResponse.json({ ...ORDER, status: "quote" })),
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

  it("falls back to the default page height when the measured content height is zero (jsdom has no layout engine, so every render takes this path, the same as a real browser's instant before its first measured paint)", async () => {
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/work-orders/order-1", () => HttpResponse.json(ORDER)),
    );
    const { container } = renderPage();
    await screen.findByText("Orden #42");
    const styleTag = container.querySelector("style");
    expect(styleTag?.textContent).toContain("58mm 297mm");
  });

  it("applies the measured page height once a valid rendered height is available, instead of always keeping the fallback", async () => {
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/work-orders/order-1", () => HttpResponse.json(ORDER)),
    );
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue(new DOMRect(0, 0, 0, 384));
    const { container } = renderPage();
    await screen.findByText("Orden #42");
    const styleTag = container.querySelector("style");
    // 384px / (96px/inch / 25.4mm/inch) = 101.6mm.
    expect(styleTag?.textContent).toContain("58mm 101.6mm");
    expect(styleTag?.textContent).not.toContain("297mm");
  });
});

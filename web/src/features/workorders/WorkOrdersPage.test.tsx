import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { WorkOrdersPage } from "./WorkOrdersPage";
import type { WorkOrderSummaryOut } from "./api";

function summary(overrides: Partial<WorkOrderSummaryOut>): WorkOrderSummaryOut {
  return {
    id: "order-1",
    number: 1,
    status: "quote",
    vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
    customer: { id: "c1", full_name: "María Hernández" },
    total_cents: 0,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function mockSessionAndOrders() {
  server.use(
    http.get("/api/auth/me", () =>
      HttpResponse.json({
        user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
        workshop: { id: "w1", name: "Taller Ana" },
      }),
    ),
    http.get("/api/work-orders", ({ request }) => {
      const statusGroup = new URL(request.url).searchParams.get("status_group");
      if (statusGroup === "closed") {
        return HttpResponse.json([summary({ id: "order-2", number: 2, status: "delivered" })]);
      }
      return HttpResponse.json([summary({ id: "order-1", number: 1, status: "quote" })]);
    }),
  );
}

function renderWorkOrdersPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/ordenes"]}>
      <Routes>
        <Route path="/ordenes" element={<WorkOrdersPage />} />
        <Route path="/ordenes/:id" element={<div>Detalle de orden</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("WorkOrdersPage", () => {
  it("renders the Abiertas tab by default, and the Historial tab's own orders on tap", async () => {
    // Defect this catches: the tabs not actually filtering by
    // `status_group` (showing the same list under both), or a tab switch
    // leaving the previous tab's orders on screen alongside the new ones.
    mockSessionAndOrders();
    const user = userEvent.setup();
    renderWorkOrdersPage();

    expect(await screen.findByText("Orden #1")).toBeInTheDocument();
    expect(screen.queryByText("Orden #2")).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Historial" }));

    expect(await screen.findByText("Orden #2")).toBeInTheDocument();
    expect(screen.queryByText("Orden #1")).not.toBeInTheDocument();
  });
});

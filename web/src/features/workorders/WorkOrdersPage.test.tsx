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

  it("moves and selects tabs with the arrow keys, wrapping at either end (roving tabindex)", async () => {
    // Defect this catches: the tabs having no keyboard navigation at all --
    // ArrowLeft/ArrowRight doing nothing, and every tab staying in the Tab
    // order at once (every tab at `tabIndex 0`) instead of following the
    // ARIA tabs roving-tabindex pattern a keyboard/screen-reader user
    // depends on.
    mockSessionAndOrders();
    const user = userEvent.setup();
    renderWorkOrdersPage();

    const openTab = await screen.findByRole("tab", { name: "Abiertas" });
    const historyTab = screen.getByRole("tab", { name: "Historial" });
    expect(openTab).toHaveAttribute("tabindex", "0");
    expect(historyTab).toHaveAttribute("tabindex", "-1");

    openTab.focus();
    await user.keyboard("{ArrowRight}");

    expect(historyTab).toHaveFocus();
    expect(historyTab).toHaveAttribute("tabindex", "0");
    expect(openTab).toHaveAttribute("tabindex", "-1");
    expect(await screen.findByText("Orden #2")).toBeInTheDocument();

    await user.keyboard("{ArrowRight}");

    expect(openTab).toHaveFocus();
    expect(openTab).toHaveAttribute("aria-selected", "true");
    expect(await screen.findByText("Orden #1")).toBeInTheDocument();
  });

  it("moves and selects tabs with ArrowLeft, wrapping from the first tab to the last", async () => {
    // Defect this catches: the sibling test above never presses ArrowLeft,
    // so a handler that silently ignored it (e.g. only branching on
    // `event.key === "ArrowRight"` and never checking for `"ArrowLeft"`
    // at all) stayed green with full coverage reporting the key untested.
    mockSessionAndOrders();
    const user = userEvent.setup();
    renderWorkOrdersPage();

    const openTab = await screen.findByRole("tab", { name: "Abiertas" });
    const historyTab = screen.getByRole("tab", { name: "Historial" });
    expect(openTab).toHaveAttribute("tabindex", "0");

    openTab.focus();
    await user.keyboard("{ArrowLeft}");

    expect(historyTab).toHaveFocus();
    expect(historyTab).toHaveAttribute("tabindex", "0");
    expect(historyTab).toHaveAttribute("aria-selected", "true");
    expect(openTab).toHaveAttribute("tabindex", "-1");
    expect(await screen.findByText("Orden #2")).toBeInTheDocument();

    await user.keyboard("{ArrowLeft}");

    expect(openTab).toHaveFocus();
    expect(openTab).toHaveAttribute("aria-selected", "true");
    expect(await screen.findByText("Orden #1")).toBeInTheDocument();
  });

  it("shows the offline message, not the empty state, when the first load settles into network_error while already offline", async () => {
    // Defect this catches: branching only on `orders.isPending` falls
    // straight through to `WorkOrderList`'s own empty state the instant the
    // query settles into its error state -- which a cold load that starts
    // offline does almost immediately -- showing "Todavía no hay órdenes"
    // as if this workshop genuinely had none, the same bug
    // `NewWorkOrderPage`'s customer/vehicle steps had.
    server.use(
      http.get("/api/auth/me", () =>
        HttpResponse.json({
          user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
          workshop: { id: "w1", name: "Taller Ana" },
        }),
      ),
      http.get("/api/work-orders", () => HttpResponse.error()),
    );
    Object.defineProperty(window.navigator, "onLine", { configurable: true, get: () => false });

    try {
      renderWorkOrdersPage();

      expect(await screen.findByText("Conéctese a internet para ver sus órdenes.")).toBeInTheDocument();
      expect(screen.queryByText("Todavía no hay órdenes")).not.toBeInTheDocument();
    } finally {
      Reflect.deleteProperty(window.navigator, "onLine");
    }
  });
});

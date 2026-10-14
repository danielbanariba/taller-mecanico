import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { server } from "../../test/server";
import { renderWithQueryClient } from "../../test/render";
import { ArchivedItemsPage } from "./ArchivedItemsPage";
import type { ItemOut } from "./api";

const SESSION_RESPONSE = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

function item(overrides: Partial<ItemOut>): ItemOut {
  return {
    id: "item-1",
    name: "Filtro de aceite",
    category: "Filtros",
    unit: "unidad",
    min_stock: 0,
    sale_price_cents: null,
    notes: null,
    stock: 10,
    needs_review: false,
    is_low: false,
    archived_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function mockSession() {
  server.use(http.get("/api/auth/me", () => HttpResponse.json(SESSION_RESPONSE)));
}

function renderArchivedItemsPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/inventario/archivados"]}>
      <Routes>
        <Route path="/inventario/archivados" element={<ArchivedItemsPage />} />
        <Route path="/inventario/:id" element={<div>Pantalla de detalle</div>} />
        <Route path="/inventario" element={<div>Pantalla de inventario</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ArchivedItemsPage", () => {
  it("lists only archived items, not active ones", async () => {
    // Defect this catches: showing every item the include_archived listing
    // returns (active and archived mixed together) instead of filtering to
    // archived ones, which would make this "archived" screen indistinguishable
    // from the normal inventory list.
    mockSession();
    server.use(
      http.get("/api/inventory/items", () =>
        HttpResponse.json([
          item({ id: "active-1", name: "Filtro activo", archived_at: null }),
          item({ id: "archived-1", name: "Filtro archivado", archived_at: "2026-01-02T00:00:00Z" }),
        ]),
      ),
    );
    renderArchivedItemsPage();

    expect(await screen.findByText("Filtro archivado")).toBeInTheDocument();
    expect(screen.queryByText("Filtro activo")).not.toBeInTheDocument();
  });

  it("shows an empty message when nothing is archived", async () => {
    mockSession();
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([item({})])));
    renderArchivedItemsPage();

    expect(await screen.findByText("No hay repuestos archivados.")).toBeInTheDocument();
  });

  it("links each archived row to the item's detail screen", async () => {
    mockSession();
    server.use(
      http.get("/api/inventory/items", () =>
        HttpResponse.json([
          item({ id: "archived-1", name: "Filtro archivado", archived_at: "2026-01-02T00:00:00Z" }),
        ]),
      ),
    );
    renderArchivedItemsPage();

    const link = await screen.findByRole("link", { name: /Filtro archivado/ });
    expect(link).toHaveAttribute("href", "/inventario/archived-1");
  });
});

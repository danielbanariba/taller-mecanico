import { describe, expect, it } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { sessionQueryKey } from "../auth/hooks";
import { server } from "../../test/server";
import { renderWithQueryClient } from "../../test/render";
import { EditItemPage } from "./EditItemPage";
import { itemQueryKey, useItem } from "./hooks";
import { ItemDetailPage } from "./ItemDetailPage";
import type { ItemOut } from "./api";

const ITEM: ItemOut = {
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
};

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

/** Exposes the item query's status, so a test knows the page has rendered the failed refetch. */
function ItemQueryStatus() {
  const item = useItem("item-1");
  return <span data-testid="item-query-status">{item.status}</span>;
}

function renderEditPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/inventario/item-1/editar"]}>
      <Routes>
        <Route path="/inventario/:id/editar" element={<EditItemPage />} />
        <Route path="/inventario" element={<div>Pantalla de inventario</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("EditItemPage", () => {
  it("shows the Spanish not-found message with a way back to the list for a 404", async () => {
    // Defect this catches: the not-found state had no way back to the
    // list, leaving the mechanic stuck on a dead-end screen (the detail
    // page already got one in T5b).
    server.use(
      http.get("/api/auth/me", () =>
        HttpResponse.json({
          user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
          workshop: { id: "w1", name: "Taller Ana" },
        }),
      ),
    );
    server.use(
      http.get("/api/inventory/items/item-1", () =>
        HttpResponse.json({ detail: "item_not_found" }, { status: 404 }),
      ),
    );
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([])));

    renderEditPage();

    expect(await screen.findByText("No se encontró el repuesto.")).toBeInTheDocument();
    const backLink = screen.getByRole("link", { name: /volver al inventario/i });
    expect(backLink).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(backLink);
    expect(await screen.findByText("Pantalla de inventario")).toBeInTheDocument();
  });

  it("keeps showing the cached item's form when refetching it fails for lack of connection", async () => {
    // Defect this catches: same as on the detail page -- a failed refetch
    // over a cached item showed "No se encontró el repuesto." instead of
    // the item, after a reload offline.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.error()),
      http.get("/api/inventory/items/item-1", () => HttpResponse.error()),
      http.get("/api/inventory/items", () => HttpResponse.error()),
    );
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(sessionQueryKey, SESSION);
    queryClient.setQueryData(itemQueryKey("item-1"), ITEM);

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/inventario/item-1/editar"]}>
          <ItemQueryStatus />
          <Routes>
            <Route path="/inventario/:id/editar" element={<EditItemPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("item-query-status")).toHaveTextContent("error"));

    expect(screen.getByLabelText(/^nombre$/i)).toHaveValue("Filtro de aceite");
    expect(screen.queryByText("No se encontró el repuesto.")).not.toBeInTheDocument();
  });

  it("disables saving and explains why when opened after the connection dropped", async () => {
    // Defect this catches (T8): each screen re-read `navigator.onLine` when
    // it mounted, so an edit form opened after the `offline` event, in a
    // browser where `navigator.onLine` had not caught up yet, stayed
    // enabled with no message while the banner already said offline.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/inventory/items/item-1", () => HttpResponse.json(ITEM)),
      http.get("/api/inventory/items/item-1/movements", () => HttpResponse.json([])),
    );
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter initialEntries={["/inventario/item-1"]}>
        <Routes>
          <Route path="/inventario/:id" element={<ItemDetailPage />} />
          <Route path="/inventario/:id/editar" element={<EditItemPage />} />
        </Routes>
      </MemoryRouter>,
    );
    await screen.findByText("10");

    act(() => {
      window.dispatchEvent(new Event("offline"));
    });
    await user.click(screen.getByRole("link", { name: "Editar" }));

    expect(await screen.findByText("Conéctese a internet para editar repuestos.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar cambios" })).toBeDisabled();
  });
});

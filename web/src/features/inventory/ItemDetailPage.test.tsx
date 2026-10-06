import { describe, expect, it } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { server } from "../../test/server";
import { renderWithQueryClient } from "../../test/render";
import { ItemDetailPage } from "./ItemDetailPage";
import type { ItemOut, MovementOut } from "./api";

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

function movement(overrides: Partial<MovementOut>): MovementOut {
  return {
    id: "mv-1",
    item_id: "item-1",
    kind: "in",
    quantity: 1,
    delta: 1,
    note: null,
    occurred_at: "2026-01-01T00:00:00Z",
    recorded_at: "2026-01-01T00:00:00Z",
    created_by: "u1",
    ...overrides,
  };
}

function mockItemAndMovements(movements: MovementOut[] = []) {
  // useRecordMovement/useItem need the session's workshop id to tag and
  // fold outbox entries (see T6); ItemDetailPage always renders behind
  // RequireSession in the real app, so every test mocks it too.
  server.use(
    http.get("/api/auth/me", () =>
      HttpResponse.json({
        user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
        workshop: { id: "w1", name: "Taller Ana" },
      }),
    ),
  );
  server.use(http.get("/api/inventory/items/item-1", () => HttpResponse.json(ITEM)));
  server.use(http.get("/api/inventory/items/item-1/movements", () => HttpResponse.json(movements)));
}

function renderDetailPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/inventario/item-1"]}>
      <Routes>
        <Route path="/inventario/:id" element={<ItemDetailPage />} />
        <Route path="/inventario" element={<div>Pantalla de inventario</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ItemDetailPage", () => {
  it("sends an adjust movement with the counted quantity from 'Contar'", async () => {
    mockItemAndMovements();
    let capturedBody: Record<string, unknown> | undefined;
    server.use(
      http.put("/api/inventory/movements/:movementId", async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          movement: movement({ kind: "adjust", quantity: 7, delta: -3 }),
          item: { id: "item-1", stock: 7, needs_review: false, is_low: false },
        });
      }),
    );
    const user = userEvent.setup();
    renderDetailPage();

    await screen.findByText("10");
    await user.click(screen.getByRole("button", { name: "Contar" }));
    const countField = await screen.findByLabelText(/cantidad contada/i);
    await user.clear(countField);
    await user.type(countField, "7");
    await user.click(screen.getByRole("button", { name: "Guardar conteo" }));

    // The optimistic update renders "7" immediately; the actual PUT lands a
    // few ticks later (it goes through the outbox write and the flush lock
    // first -- see T6), so the request body is asserted via `waitFor`
    // rather than right after the optimistic render settles.
    expect(await screen.findByText("7")).toBeInTheDocument();
    await waitFor(() => expect(capturedBody).toMatchObject({ item_id: "item-1", kind: "adjust", quantity: 7 }));
  });

  it("renders the movement history newest first with Spanish labels", async () => {
    mockItemAndMovements([
      movement({ id: "mv-newest", kind: "out", quantity: 1, delta: -1 }),
      movement({ id: "mv-oldest", kind: "in", quantity: 3, delta: 3 }),
    ]);
    renderDetailPage();

    const entries = await screen.findAllByText(/^(Entrada|Salida|Conteo)/);
    expect(entries).toHaveLength(2);
    expect(entries[0]).toHaveTextContent("Salida −1");
    expect(entries[1]).toHaveTextContent("Entrada +3");
  });

  it("asks for confirmation before archiving, then sends the archive request and returns to the list", async () => {
    mockItemAndMovements();
    let archiveWasCalled = false;
    server.use(
      http.post("/api/inventory/items/item-1/archive", () => {
        archiveWasCalled = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderDetailPage();

    await screen.findByText("10");
    await user.click(screen.getByRole("button", { name: "Archivar" }));

    const dialog = await screen.findByRole("dialog", { name: "Archivar repuesto" });
    expect(archiveWasCalled).toBe(false);

    await user.click(within(dialog).getByRole("button", { name: "Archivar" }));

    expect(await screen.findByText("Pantalla de inventario")).toBeInTheDocument();
    expect(archiveWasCalled).toBe(true);
  });

  it("renders the edit action as a single link, not a button nested inside one", async () => {
    // Defect this catches: a <button> rendered inside an <a> is invalid
    // HTML and gives assistive tech and keyboard users two overlapping
    // interactive elements with the same accessible name instead of one.
    mockItemAndMovements();
    renderDetailPage();

    await screen.findByText("10");

    expect(screen.getByRole("link", { name: "Editar" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Editar" })).not.toBeInTheDocument();
  });

  it("shows the Spanish not-found message with a way back to the list for a 404", async () => {
    // Defect this catches: the not-found state had no way back to the
    // list, leaving the mechanic stuck on a dead-end screen.
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
    renderDetailPage();

    expect(await screen.findByText("No se encontró el repuesto.")).toBeInTheDocument();
    const backLink = screen.getByRole("link", { name: /volver al inventario/i });
    expect(backLink).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(backLink);
    expect(await screen.findByText("Pantalla de inventario")).toBeInTheDocument();
  });
});

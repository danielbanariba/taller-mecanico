import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { server } from "../../test/server";
import { renderWithQueryClient } from "../../test/render";
import { NewItemPage } from "./NewItemPage";

function mockEmptyItemsList() {
  server.use(http.get("/api/inventory/items", () => HttpResponse.json([])));
}

function renderNewItemPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/inventario/nuevo"]}>
      <Routes>
        <Route path="/inventario/nuevo" element={<NewItemPage />} />
        <Route path="/inventario/:id" element={<div>Pantalla de detalle</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("NewItemPage", () => {
  it("blocks submission when the name is missing, without calling the API", async () => {
    mockEmptyItemsList();
    let apiWasCalled = false;
    server.use(
      http.post("/api/inventory/items", () => {
        apiWasCalled = true;
        return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
      }),
    );
    const user = userEvent.setup();
    renderNewItemPage();

    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(await screen.findByText("El nombre es obligatorio.")).toBeInTheDocument();
    expect(apiWasCalled).toBe(false);
  });

  it("sends a client-generated id, the typed initial_stock and a price converted to integer cents", async () => {
    mockEmptyItemsList();
    let capturedBody: Record<string, unknown> | undefined;
    server.use(
      http.post("/api/inventory/items", async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(
          {
            id: capturedBody.id,
            name: capturedBody.name,
            category: null,
            unit: "unidad",
            min_stock: 0,
            sale_price_cents: capturedBody.sale_price_cents ?? null,
            notes: null,
            stock: capturedBody.initial_stock ?? 0,
            needs_review: false,
            is_low: false,
            archived_at: null,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
          { status: 201 },
        );
      }),
    );
    const user = userEvent.setup();
    renderNewItemPage();

    await user.type(screen.getByLabelText(/^nombre$/i), "Filtro de aire");
    const initialStockField = screen.getByLabelText(/cantidad actual/i);
    await user.clear(initialStockField);
    await user.type(initialStockField, "4");
    await user.type(screen.getByLabelText(/precio de venta/i), "125.50");
    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(await screen.findByText("Pantalla de detalle")).toBeInTheDocument();
    expect(capturedBody?.id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    expect(capturedBody?.name).toBe("Filtro de aire");
    expect(capturedBody?.initial_stock).toBe(4);
    expect(capturedBody?.sale_price_cents).toBe(12550);
  });

  it("shows the Spanish message for item_name_taken on a 409", async () => {
    mockEmptyItemsList();
    server.use(
      http.post("/api/inventory/items", () =>
        HttpResponse.json({ detail: "item_name_taken" }, { status: 409 }),
      ),
    );
    const user = userEvent.setup();
    renderNewItemPage();

    await user.type(screen.getByLabelText(/^nombre$/i), "Filtro de aire");
    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(await screen.findByText("Ya existe un repuesto con ese nombre.")).toBeInTheDocument();
  });

  it("disables submission and explains why when offline, without calling the API", async () => {
    // Defect this catches: creating an item has no client-generated-id
    // conflict recovery for a server round trip that can never happen
    // offline in this MVP, so letting the form submit anyway would just
    // hang on a network_error with no clear explanation.
    mockEmptyItemsList();
    let apiWasCalled = false;
    server.use(
      http.post("/api/inventory/items", () => {
        apiWasCalled = true;
        return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
      }),
    );
    const originalOnLine = Object.getOwnPropertyDescriptor(window.navigator, "onLine");
    Object.defineProperty(window.navigator, "onLine", { value: false, configurable: true });
    try {
      const user = userEvent.setup();
      renderNewItemPage();

      await user.type(screen.getByLabelText(/^nombre$/i), "Filtro de aire");
      expect(screen.getByText("Conéctese a internet para agregar repuestos.")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /guardar repuesto/i })).toBeDisabled();

      await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));
      expect(apiWasCalled).toBe(false);
    } finally {
      if (originalOnLine) {
        Object.defineProperty(window.navigator, "onLine", originalOnLine);
      }
    }
  });
});

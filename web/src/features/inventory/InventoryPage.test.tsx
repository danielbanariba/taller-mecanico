import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { server } from "../../test/server";
import { renderWithQueryClient } from "../../test/render";
import { InventoryPage } from "./InventoryPage";
import type { ItemOut } from "./api";

const SESSION_RESPONSE = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

function baseItem(overrides: Partial<ItemOut>): ItemOut {
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
  server.use(http.get("/api/auth/me", () => HttpResponse.json(SESSION_RESPONSE, { status: 200 })));
}

function renderInventoryPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/inventario"]}>
      <Routes>
        <Route path="/inventario" element={<InventoryPage />} />
        <Route path="/inventario/nuevo" element={<div>Pantalla de nuevo repuesto</div>} />
        <Route path="/inventario/:id" element={<div>Pantalla de detalle</div>} />
        <Route path="/login" element={<div>Pantalla de inicio de sesión</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("InventoryPage", () => {
  afterEach(() => {
    // Safety net: a test that fails before reaching its own cleanup must
    // not leave fake timers active for every test that runs after it.
    vi.useRealTimers();
  });

  it("renders the stock number and the 'Por acabarse' badge for low stock", async () => {
    mockSession();
    server.use(
      http.get("/api/inventory/items", () =>
        HttpResponse.json([baseItem({ id: "low", name: "Bujía", stock: 2, min_stock: 5, is_low: true })]),
      ),
    );

    renderInventoryPage();

    const row = (await screen.findByText("Bujía")).closest("li");
    expect(row).not.toBeNull();
    expect(within(row as HTMLElement).getByText("2")).toBeInTheDocument();
    expect(within(row as HTMLElement).getByText("Por acabarse")).toBeInTheDocument();
  });

  it("renders the 'Revisar' badge for negative stock instead of 'Por acabarse'", async () => {
    mockSession();
    server.use(
      http.get("/api/inventory/items", () =>
        HttpResponse.json([
          baseItem({ id: "neg", name: "Banda", stock: -3, min_stock: 5, is_low: true, needs_review: true }),
        ]),
      ),
    );

    renderInventoryPage();

    const row = (await screen.findByText("Banda")).closest("li");
    expect(row).not.toBeNull();
    expect(within(row as HTMLElement).getByText("-3")).toBeInTheDocument();
    expect(within(row as HTMLElement).getByText("Revisar")).toBeInTheDocument();
    expect(within(row as HTMLElement).queryByText("Por acabarse")).not.toBeInTheDocument();
  });

  it("requests low_stock=true when 'Por acabarse' is tapped", async () => {
    mockSession();
    let lastLowStockParam: string | null = null;
    server.use(
      http.get("/api/inventory/items", ({ request }) => {
        lastLowStockParam = new URL(request.url).searchParams.get("low_stock");
        return HttpResponse.json([baseItem({})]);
      }),
    );
    const user = userEvent.setup();
    renderInventoryPage();

    await screen.findByText("10");
    await user.click(screen.getByRole("button", { name: "Por acabarse" }));

    await waitFor(() => expect(lastLowStockParam).toBe("true"));
  });

  it("requests q after the search debounce settles", async () => {
    mockSession();
    const requestedQueries: Array<string | null> = [];
    server.use(
      http.get("/api/inventory/items", ({ request }) => {
        requestedQueries.push(new URL(request.url).searchParams.get("q"));
        return HttpResponse.json([baseItem({})]);
      }),
    );
    renderInventoryPage();
    await screen.findByText("10");

    fireEvent.change(screen.getByLabelText("Buscar repuesto"), { target: { value: "filtro" } });

    // No request with the typed query yet: the 300ms debounce has not settled.
    expect(requestedQueries).not.toContain("filtro");

    await waitFor(() => expect(requestedQueries).toContain("filtro"), { timeout: 1000 });
  });

  it("opens the detail screen when the row is tapped, not when a stepper button is tapped", async () => {
    mockSession();
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([baseItem({})])));
    server.use(http.put("/api/inventory/movements/:movementId", () => new Promise<Response>(() => {})));
    const user = userEvent.setup();
    renderInventoryPage();

    await screen.findByText("10");
    await user.click(screen.getByRole("button", { name: "Agregar una unidad de Filtro de aceite" }));
    expect(screen.queryByText("Pantalla de detalle")).not.toBeInTheDocument();

    await user.click(screen.getByText("Filtro de aceite"));
    expect(await screen.findByText("Pantalla de detalle")).toBeInTheDocument();
  });

  it("increments stock optimistically and sends a PUT with a fresh movement id", async () => {
    mockSession();
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([baseItem({ stock: 5 })])));
    let capturedBody: unknown;
    let capturedMovementId: string | undefined;
    server.use(
      http.put("/api/inventory/movements/:movementId", async ({ request, params }) => {
        capturedBody = await request.json();
        capturedMovementId = params.movementId as string;
        return HttpResponse.json(
          {
            movement: {
              id: capturedMovementId,
              item_id: "item-1",
              kind: "in",
              quantity: 1,
              delta: 1,
              note: null,
              occurred_at: "2026-01-02T00:00:00Z",
              recorded_at: "2026-01-02T00:00:00Z",
              created_by: "u1",
            },
            item: { id: "item-1", stock: 6, needs_review: false, is_low: false },
          },
          { status: 201 },
        );
      }),
    );
    const user = userEvent.setup();
    renderInventoryPage();

    await screen.findByText("5");
    await user.click(screen.getByRole("button", { name: "Agregar una unidad de Filtro de aceite" }));

    // Optimistic: the stock already moved before the mocked response above resolved.
    expect(await screen.findByText("6")).toBeInTheDocument();
    await waitFor(() => expect(capturedMovementId).toMatch(/^[0-9a-f-]{36}$/));
    expect(capturedBody).toMatchObject({ item_id: "item-1", kind: "in", quantity: 1 });
  });

  it("rolls back the stock and shows an error when the movement request fails", async () => {
    mockSession();
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([baseItem({ stock: 5 })])));
    server.use(
      http.put("/api/inventory/movements/:movementId", () =>
        HttpResponse.json({ detail: "stock_out_of_range" }, { status: 422 }),
      ),
    );
    const user = userEvent.setup();
    renderInventoryPage();

    await screen.findByText("5");
    await user.click(screen.getByRole("button", { name: "Agregar una unidad de Filtro de aceite" }));

    expect(await screen.findByText("5")).toBeInTheDocument();
    expect(await screen.findByText("La cantidad ingresada no es válida.")).toBeInTheDocument();
  });

  it("sends a different movement id for each of two taps", async () => {
    mockSession();
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([baseItem({ stock: 5 })])));
    const capturedIds: string[] = [];
    server.use(
      http.put("/api/inventory/movements/:movementId", ({ params }) => {
        capturedIds.push(params.movementId as string);
        return HttpResponse.json({
          movement: {
            id: params.movementId,
            item_id: "item-1",
            kind: "in",
            quantity: 1,
            delta: 1,
            note: null,
            occurred_at: "2026-01-02T00:00:00Z",
            recorded_at: "2026-01-02T00:00:00Z",
            created_by: "u1",
          },
          item: { id: "item-1", stock: 6, needs_review: false, is_low: false },
        });
      }),
    );
    const user = userEvent.setup();
    renderInventoryPage();

    await screen.findByText("5");
    const incrementButton = screen.getByRole("button", { name: "Agregar una unidad de Filtro de aceite" });
    await user.click(incrementButton);
    await user.click(incrementButton);

    await waitFor(() => expect(capturedIds).toHaveLength(2));
    expect(capturedIds[0]).not.toBe(capturedIds[1]);
  });
});

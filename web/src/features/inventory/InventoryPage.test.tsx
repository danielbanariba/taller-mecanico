import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { delay, http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { server } from "../../test/server";
import { renderWithQueryClient } from "../../test/render";
import { AppShell } from "../../app/AppShell";
import { sessionQueryKey } from "../auth/hooks";
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

/**
 * `InventoryPage` nested under `AppShell`, like `router.tsx` does: the
 * workshop heading these tests assert on now comes from the shell, not
 * the page.
 */
function inventoryRoutes() {
  return (
    <MemoryRouter initialEntries={["/inventario"]}>
      <Routes>
        <Route path="/login" element={<div>Pantalla de inicio de sesión</div>} />
        <Route element={<AppShell />}>
          <Route path="/inventario" element={<InventoryPage />} />
          <Route path="/inventario/nuevo" element={<div>Pantalla de nuevo repuesto</div>} />
          <Route path="/inventario/:id" element={<div>Pantalla de detalle</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

function renderInventoryPage() {
  return renderWithQueryClient(inventoryRoutes());
}

describe("InventoryPage", () => {
  afterEach(() => {
    // Safety net: a test that fails before reaching its own cleanup must
    // not leave fake timers active for every test that runs after it.
    vi.useRealTimers();
  });

  it("never shows another workshop's cached items once the session belongs to a different workshop", async () => {
    // Defect this catches: inventory query keys that are not scoped by
    // workshop. When the session changes workshop without this tab's cache
    // being cleared (the cookie replaced from another tab, for one), the
    // new workshop's screen is served the previous workshop's cached list.
    const otherWorkshopSession = {
      user: { id: "u2", full_name: "Beto Díaz", phone: "88887777", role: "owner" },
      workshop: { id: "w2", name: "Taller Beto" },
    };
    let session = SESSION_RESPONSE;
    let releaseOtherWorkshopItems = () => {};
    const otherWorkshopItemsReady = new Promise<void>((resolve) => {
      releaseOtherWorkshopItems = resolve;
    });
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(session)),
      http.get("/api/inventory/items", async () => {
        if (session === SESSION_RESPONSE) {
          return HttpResponse.json([baseItem({ name: "Filtro de Ana" })]);
        }
        await otherWorkshopItemsReady;
        return HttpResponse.json([baseItem({ id: "item-2", name: "Bujía de Beto" })]);
      }),
    );
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={queryClient}>{inventoryRoutes()}</QueryClientProvider>);
    await screen.findByText("Filtro de Ana");

    session = otherWorkshopSession;
    await queryClient.invalidateQueries({ queryKey: sessionQueryKey });

    expect(await screen.findByText("Taller Beto")).toBeInTheDocument();
    expect(screen.queryByText("Filtro de Ana")).not.toBeInTheDocument();
    releaseOtherWorkshopItems();
    expect(await screen.findByText("Bujía de Beto")).toBeInTheDocument();
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
    // Resolves, but not instantly: the assertion right after the click
    // still runs while the request (and the outbox flush behind it) is in
    // flight, without leaving a PUT permanently unresolved -- a mock that
    // never resolves would hold the outbox's single flush lock forever and
    // deadlock every later test in this file.
    server.use(
      http.put("/api/inventory/movements/:movementId", async () => {
        await delay(50);
        return HttpResponse.json({
          movement: {
            id: "m1",
            item_id: "item-1",
            kind: "in",
            quantity: 1,
            delta: 1,
            note: null,
            occurred_at: "2026-01-02T00:00:00Z",
            recorded_at: "2026-01-02T00:00:00Z",
            created_by: "u1",
          },
          item: { id: "item-1", stock: 11, needs_review: false, is_low: false },
        });
      }),
    );
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

  it("keeps showing the optimistic stock when the movement is queued (network down)", async () => {
    // Defect this catches: treating a queued (offline) result the same as
    // an error would roll the optimistic stock back to its pre-tap value
    // even though nothing was actually rejected -- the movement is just
    // waiting to be sent.
    mockSession();
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([baseItem({ stock: 5 })])));
    server.use(http.put("/api/inventory/movements/:movementId", () => HttpResponse.error()));
    const user = userEvent.setup();
    renderInventoryPage();

    await screen.findByText("5");
    await user.click(screen.getByRole("button", { name: "Agregar una unidad de Filtro de aceite" }));

    expect(await screen.findByText("6")).toBeInTheDocument();
    // Give the (failing) flush attempt a moment to actually run and settle
    // as "queued" rather than an error, then confirm the stock is still 6,
    // not rolled back to 5.
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.queryByText("Ocurrió un error. Intente de nuevo.")).not.toBeInTheDocument();
  });

  it("ends with the correct final stock when two rapid taps' server responses would resolve in reverse order", async () => {
    // Defect this catches (the out-of-order reconciliation bug found in
    // the T5 review): if each tap sent its own independent, unsynchronized
    // PUT, a slow first response arriving after a fast second response
    // could overwrite the cache back to the first (now-stale) value. Since
    // every send goes through the single FIFO outbox flush, the server
    // never has two of this item's movement PUTs in flight at once, so the
    // responses can never be reconciled out of order.
    mockSession();
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([baseItem({ stock: 5 })])));

    let requestNumber = 0;
    let inFlight = 0;
    let maxInFlight = 0;
    server.use(
      http.put("/api/inventory/movements/:movementId", async ({ params }) => {
        requestNumber += 1;
        const isFirstRequest = requestNumber === 1;
        inFlight += 1;
        maxInFlight = Math.max(maxInFlight, inFlight);
        // The first request the server receives is deliberately the
        // slower one to resolve; the old (buggy) direct-PUT design would
        // let the second tap's fast response land first, then have the
        // first tap's late response overwrite it afterwards.
        await delay(isFirstRequest ? 40 : 5);
        inFlight -= 1;
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
          item: { id: "item-1", stock: isFirstRequest ? 6 : 7, needs_review: false, is_low: false },
        });
      }),
    );
    const user = userEvent.setup();
    renderInventoryPage();

    await screen.findByText("5");
    const incrementButton = screen.getByRole("button", { name: "Agregar una unidad de Filtro de aceite" });
    await user.click(incrementButton);
    await user.click(incrementButton);

    await waitFor(() => expect(requestNumber).toBe(2));
    await waitFor(() => expect(screen.getByText("7")).toBeInTheDocument());
    expect(maxInFlight).toBe(1);
    // Give any trailing reconciliation one more tick, then confirm the
    // second (later, authoritative) response's stock is still the one
    // shown -- the defect this regression test targets would show "6" here.
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(screen.getByText("7")).toBeInTheDocument();
  });
});

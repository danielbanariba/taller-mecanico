import { afterEach, describe, expect, it } from "vitest";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { sessionQueryKey } from "../auth/hooks";
import { server } from "../../test/server";
import { renderWithQueryClient } from "../../test/render";
import { itemQueryKey, useItem } from "./hooks";
import { ItemDetailPage } from "./ItemDetailPage";
import { OfflineStatusBanner } from "./OfflineStatusBanner";
import { defaultOutbox } from "./outbox";
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
    order_id: null,
    order_line_id: null,
    order_number: null,
    ...overrides,
  };
}

function mockItemAndMovements(movements: MovementOut[] = [], item: ItemOut = ITEM) {
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
  server.use(http.get("/api/inventory/items/item-1", () => HttpResponse.json(item)));
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

/** The detail page plus the status banner `RequireSession` renders above every protected screen. */
function renderDetailPageWithBanner() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/inventario/item-1"]}>
      <OfflineStatusBanner workshopId="w1" />
      <Routes>
        <Route path="/inventario/:id" element={<ItemDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

/** Exposes the item query's status, so a test knows the page has rendered the failed refetch. */
function ItemQueryStatus() {
  const item = useItem("item-1");
  return <span data-testid="item-query-status">{item.status}</span>;
}

/**
 * Renders the page over a cache that already holds the session and the
 * item -- what a reload restores from IndexedDB -- while every request
 * fails as it does without a connection.
 */
function renderDetailPageFromCacheWithoutConnection() {
  server.use(
    http.get("/api/auth/me", () => HttpResponse.error()),
    http.get("/api/inventory/items/item-1", () => HttpResponse.error()),
    http.get("/api/inventory/items/item-1/movements", () => HttpResponse.error()),
  );
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  queryClient.setQueryData(sessionQueryKey, {
    user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
    workshop: { id: "w1", name: "Taller Ana" },
  });
  queryClient.setQueryData(itemQueryKey("w1", "item-1"), ITEM);

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/inventario/item-1"]}>
        <ItemQueryStatus />
        <Routes>
          <Route path="/inventario/:id" element={<ItemDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

/** What a real browser does when the connection drops: `navigator.onLine` turns false and `offline` fires. */
function goOffline() {
  Object.defineProperty(window.navigator, "onLine", { value: false, configurable: true });
  act(() => {
    window.dispatchEvent(new Event("offline"));
  });
}

afterEach(() => {
  // Drops the own-property override from `goOffline`, so jsdom's own
  // `navigator.onLine` getter (always true) applies to the next test.
  Reflect.deleteProperty(window.navigator, "onLine");
});

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

  it.each([
    ["an empty count", ""],
    ["a count over the maximum", "1000001"],
  ])("refuses to save %s and explains why, instead of recording it", async (_case, typed) => {
    // Defect this catches: the dialog coerced an empty or invalid entry to
    // 0 (and accepted any size), so clearing the field and tapping "Guardar
    // conteo" silently set the real stock to 0.
    mockItemAndMovements();
    let putCount = 0;
    server.use(
      http.put("/api/inventory/movements/:movementId", () => {
        putCount += 1;
        return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
      }),
    );
    const user = userEvent.setup();
    renderDetailPage();

    await screen.findByText("10");
    await user.click(screen.getByRole("button", { name: "Contar" }));
    const countField = await screen.findByLabelText(/cantidad contada/i);
    await user.clear(countField);
    if (typed) {
      await user.type(countField, typed);
    }
    await user.click(screen.getByRole("button", { name: "Guardar conteo" }));

    expect(await screen.findByText("Ingrese una cantidad entre 0 y 1,000,000.")).toBeInTheDocument();
    expect(countField).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(await defaultOutbox.listForWorkshop("w1")).toEqual([]);
    expect(putCount).toBe(0);
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

  it("links a movement to the order that caused it, and renders no such link for a manual one", async () => {
    // Defect this catches: the API already links a movement to the work
    // order that caused it (`order_id`/`order_number`), but the history
    // never surfaced that link, so a mechanic looking at a stock change
    // had no way to open the order that made it -- or, the opposite bug,
    // every movement grew a link even when it was never order-caused.
    mockItemAndMovements([
      movement({ id: "mv-linked", order_id: "order-1", order_line_id: "line-1", order_number: 42 }),
      movement({ id: "mv-manual" }),
    ]);
    renderDetailPage();

    const orderLinks = await screen.findAllByRole("link", { name: /^Orden #/ });
    expect(orderLinks).toHaveLength(1);
    expect(orderLinks[0]).toHaveTextContent("Orden #42");
    expect(orderLinks[0]).toHaveAttribute("href", "/ordenes/order-1");
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

  it("shows the sale price in Lempiras", async () => {
    // Defect this catches (T8): the price was stored and shown in the
    // edit form, but the detail screen never displayed it, so a mechanic
    // quoting a customer had to open the edit form to read it.
    mockItemAndMovements([], { ...ITEM, sale_price_cents: 125_000 });
    renderDetailPage();

    await screen.findByText("10");

    expect(screen.getByText(/^Precio de venta: L\s1,250\.00$/)).toBeInTheDocument();
  });

  it("omits the price line for an item without a sale price", async () => {
    // Defect this catches: formatting a missing price would show a
    // misleading "L 0.00" for an item that simply has no price yet.
    mockItemAndMovements();
    renderDetailPage();

    await screen.findByText("10");

    expect(screen.queryByText(/Precio de venta/)).not.toBeInTheDocument();
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

describe("ItemDetailPage offline", () => {
  it("writes a tap made after the browser went offline to the IndexedDB outbox", async () => {
    // Defect this catches: under TanStack Query's default `networkMode:
    // 'online'` a tap made after the `offline` event never ran its
    // mutationFn, so nothing reached the outbox; the tap lived only as a
    // paused mutation in the persisted query cache, which has no way to
    // resume it after a reload, so the movement was silently lost.
    mockItemAndMovements();
    server.use(http.put("/api/inventory/movements/:movementId", () => HttpResponse.error()));
    const user = userEvent.setup();
    renderDetailPage();

    await screen.findByText("10");
    goOffline();
    await user.click(screen.getByRole("button", { name: "Agregar una unidad de Filtro de aceite" }));

    expect(await screen.findByText("11")).toBeInTheDocument();
    await waitFor(async () => {
      const queued = await defaultOutbox.listForWorkshop("w1");
      expect(queued).toMatchObject([{ itemId: "item-1", kind: "in", quantity: 1 }]);
    });
  });

  it("shows how many changes are waiting to be sent, updated after every offline tap", async () => {
    // Defect this catches: a mechanic tapping while offline had no way to
    // tell that those taps were saved on the phone and still had to reach
    // the server (T8 saw only the generic offline message, never a count).
    mockItemAndMovements();
    server.use(http.put("/api/inventory/movements/:movementId", () => HttpResponse.error()));
    const user = userEvent.setup();
    renderDetailPageWithBanner();

    await screen.findByText("10");
    goOffline();
    const increment = screen.getByRole("button", { name: "Agregar una unidad de Filtro de aceite" });

    await user.click(increment);
    expect(await screen.findByText("1 cambio por enviar")).toBeInTheDocument();

    await user.click(increment);
    await user.click(increment);
    expect(await screen.findByText("3 cambios por enviar")).toBeInTheDocument();
    expect(screen.getByText("Sin conexión. Los cambios se guardan en el teléfono.")).toBeInTheDocument();
  });

  it("keeps showing the cached item when refetching it fails for lack of connection", async () => {
    // Defect this catches: a failed refetch flips the item query to
    // "error" while it still holds the cached item, and the page checked
    // `isError` first -- so after a reload offline the mechanic saw "No se
    // encontró el repuesto." instead of the item they had open.
    renderDetailPageFromCacheWithoutConnection();

    await waitFor(() => expect(screen.getByTestId("item-query-status")).toHaveTextContent("error"));

    expect(screen.getByRole("heading", { name: "Filtro de aceite" })).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.queryByText("No se encontró el repuesto.")).not.toBeInTheDocument();
  });

  it("disables archiving with an explanation while offline, but keeps the stock buttons usable", async () => {
    // Defect this catches: archiving needs the server (it is not an
    // outbox movement), yet "Archivar" stayed enabled offline with no
    // message, unlike creating and editing; the stepper and count must
    // stay usable because they go through the outbox.
    mockItemAndMovements();
    renderDetailPage();

    await screen.findByText("10");
    goOffline();

    expect(await screen.findByText("Conéctese a internet para archivar repuestos.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Archivar" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Agregar una unidad de Filtro de aceite" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Quitar una unidad de Filtro de aceite" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Contar" })).toBeEnabled();
  });
});

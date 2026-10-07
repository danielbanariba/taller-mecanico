import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { onlineManager, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { sessionQueryKey } from "../features/auth/hooks";
import { InventoryPage } from "../features/inventory/InventoryPage";
import { server } from "../test/server";
import { AppShell } from "./AppShell";

const SESSION_RESPONSE = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

function mockSession() {
  server.use(http.get("/api/auth/me", () => HttpResponse.json(SESSION_RESPONSE)));
}

/**
 * The shell mounted over a small slice of the real route tree: an
 * inventory detail route, a nested vehicle route, and the Órdenes tab.
 * None of their real screens are under test here -- a stub stands in for
 * each, since this file only tests the shell's own wiring (active tab,
 * logout). `/login` sits outside the shell, like in `router.tsx`.
 */
function renderShell(initialPath: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const view = render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/login" element={<div>Pantalla de inicio de sesión</div>} />
          <Route element={<AppShell />}>
            <Route path="/inventario" element={<InventoryPage />} />
            <Route path="/inventario/:id" element={<div>Detalle de repuesto</div>} />
            <Route path="/clientes/:customerId/vehiculos/:vehicleId" element={<div>Detalle de vehículo</div>} />
            <Route path="/ordenes" element={<div>Pantalla de órdenes</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return { ...view, queryClient };
}

describe("AppShell", () => {
  it("marks Inventario active, with aria-current, on a nested item route", async () => {
    // Defect this catches: a shell that only highlights the active tab on
    // an exact index match would leave every tab unmarked (or the wrong
    // one marked) on any nested screen, such as an item's own detail page.
    mockSession();
    renderShell("/inventario/item-1");

    const inventarioTab = await screen.findByRole("link", { name: "Inventario" });
    expect(inventarioTab).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Clientes" })).not.toHaveAttribute("aria-current");
    expect(screen.getByText("Detalle de repuesto")).toBeInTheDocument();
  });

  it("marks Clientes active on a nested vehicle route", async () => {
    // Defect this catches: deriving the active tab from the full path
    // instead of its first segment, which would never mark Clientes
    // active on a vehicle screen nested two levels under /clientes.
    mockSession();
    renderShell("/clientes/c1/vehiculos/v1");

    const clientesTab = await screen.findByRole("link", { name: "Clientes" });
    expect(clientesTab).toHaveAttribute("aria-current", "page");
    expect(screen.getByText("Detalle de vehículo")).toBeInTheDocument();
  });

  it("renders exactly one logout control, from the shell's 'Más' menu, not from InventoryPage", async () => {
    // Defect this catches: the move out of InventoryPage leaving a second,
    // duplicate logout button behind instead of removing the original.
    mockSession();
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([])));
    const user = userEvent.setup();
    renderShell("/inventario");

    await screen.findByText("Taller Ana");
    await user.click(screen.getByRole("button", { name: "Más" }));

    expect(screen.getAllByRole("button", { name: "Cerrar sesión" })).toHaveLength(1);
  });

  it("logs out from the 'Más' menu, clears the cached session, and redirects to /login", async () => {
    // Defect this catches: a logout wired into the shell that forgets to
    // call the logout mutation, clear the cache, or navigate away, any of
    // which would leave the previous session reachable after "logging out"
    // (e.g. a handler that only called `navigate("/login")` directly).
    let loggedOut = false;
    server.use(
      http.get("/api/auth/me", () =>
        loggedOut
          ? HttpResponse.json({ detail: "not_authenticated" }, { status: 401 })
          : HttpResponse.json(SESSION_RESPONSE),
      ),
      http.get("/api/inventory/items", () => HttpResponse.json([])),
      http.post("/api/auth/logout", () => {
        loggedOut = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    const { queryClient } = renderShell("/inventario");

    await screen.findByText("Taller Ana");
    await user.click(screen.getByRole("button", { name: "Más" }));
    await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));

    expect(await screen.findByText("Pantalla de inicio de sesión")).toBeInTheDocument();
    await waitFor(() => expect(queryClient.getQueryData(sessionQueryKey)).not.toEqual(SESSION_RESPONSE));
  });

  it("'Más' menu offers Caja del día, Exportar todo and Cerrar sesión", async () => {
    // Defect this catches: the phase-1 lone logout button never actually
    // replaced with the three phase-3 actions `design.md`'s AD-16 requires.
    mockSession();
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([])));
    const user = userEvent.setup();
    renderShell("/inventario");

    await screen.findByText("Taller Ana");
    await user.click(screen.getByRole("button", { name: "Más" }));

    expect(screen.getByRole("link", { name: "Caja del día" })).toHaveAttribute("href", "/ordenes/caja");
    expect(screen.getByRole("button", { name: "Exportar todo" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cerrar sesión" })).toBeInTheDocument();
  });

  it("disables 'Exportar todo' while offline, with the Spanish message", async () => {
    // Defect this catches: exporting attempted (or silently allowed)
    // offline, when the API it needs is unreachable anyway.
    mockSession();
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([])));
    const user = userEvent.setup();
    renderShell("/inventario");

    await screen.findByText("Taller Ana");
    // Flipped after the session has already loaded: a query's default
    // `networkMode` ("online") pauses its very first fetch while offline
    // instead of running it, so marking the manager offline before render
    // would leave the session query paused forever and "Taller Ana" would
    // never appear.
    onlineManager.setOnline(false);
    await user.click(screen.getByRole("button", { name: "Más" }));

    expect(screen.getByRole("button", { name: "Exportar todo" })).toBeDisabled();
    expect(screen.getByText("Conéctese a internet para exportar los datos.")).toBeInTheDocument();
  });

  it("'Exportar todo' downloads the ZIP through a temporary link and revokes its object URL", async () => {
    // Defect this catches: the menu button never actually wired to
    // `exportData.ts` (or wired to the wrong module), so nothing downloads.
    mockSession();
    server.use(
      http.get("/api/inventory/items", () => HttpResponse.json([])),
      http.get("/api/export", () =>
        new HttpResponse(new Blob(["zip-bytes"], { type: "application/zip" }), {
          headers: { "Content-Disposition": 'attachment; filename="taller-export-2026-10-07.zip"' },
        }),
      ),
    );
    const createObjectURL = vi.fn<(obj: Blob | MediaSource) => string>(() => "blob:mock-url");
    const revokeObjectURL = vi.fn<(url: string) => void>();
    URL.createObjectURL = createObjectURL;
    URL.revokeObjectURL = revokeObjectURL;
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    const user = userEvent.setup();
    renderShell("/inventario");

    await screen.findByText("Taller Ana");
    await user.click(screen.getByRole("button", { name: "Más" }));
    await user.click(screen.getByRole("button", { name: "Exportar todo" }));

    await waitFor(() => expect(createObjectURL).toHaveBeenCalledTimes(1));
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:mock-url");

    clickSpy.mockRestore();
  });

  it("marks Órdenes active on its route", async () => {
    // Defect this catches: a shell that only highlights Inventario/
    // Clientes, leaving the third tab permanently unmarked.
    mockSession();
    renderShell("/ordenes");

    const ordenesTab = await screen.findByRole("link", { name: "Órdenes" });
    expect(ordenesTab).toHaveAttribute("aria-current", "page");
    expect(screen.getByText("Pantalla de órdenes")).toBeInTheDocument();
  });

  it("still renders the shell and switches tabs while offline, with no network request of its own", async () => {
    // Defect this catches: tab navigation implemented through (or gated
    // behind) a network call, which would strand the user mid-tap offline
    // even though react-router's client-side navigation needs no request.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.error()),
      http.get("/api/inventory/items", () => HttpResponse.error()),
    );
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(sessionQueryKey, SESSION_RESPONSE);
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/inventario"]}>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/inventario" element={<InventoryPage />} />
              <Route path="/ordenes" element={<div>Pantalla de órdenes</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await screen.findByText("Taller Ana");
    const user = userEvent.setup();
    await user.click(screen.getByRole("link", { name: "Órdenes" }));

    expect(await screen.findByText("Pantalla de órdenes")).toBeInTheDocument();
  });
});

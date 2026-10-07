import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { sessionQueryKey } from "../features/auth/hooks";
import { InventoryPage } from "../features/inventory/InventoryPage";
import { WorkOrdersComingSoon } from "../features/workorders/WorkOrdersComingSoon";
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
 * inventory detail route, a nested vehicle route (its screen does not
 * exist until Slice 5 -- a stub stands in for it here), and the Órdenes
 * placeholder. `/login` sits outside the shell, like in `router.tsx`.
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
            <Route path="/ordenes" element={<WorkOrdersComingSoon />} />
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

  it("renders exactly one logout control, from the shell, not from InventoryPage", async () => {
    // Defect this catches: the move out of InventoryPage leaving a second,
    // duplicate logout button behind instead of removing the original.
    mockSession();
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([])));
    renderShell("/inventario");

    await screen.findByText("Taller Ana");
    expect(screen.getAllByRole("button", { name: "Cerrar sesión" })).toHaveLength(1);
  });

  it("logs out from the shell, clears the cached session, and redirects to /login", async () => {
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
    await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));

    expect(await screen.findByText("Pantalla de inicio de sesión")).toBeInTheDocument();
    await waitFor(() => expect(queryClient.getQueryData(sessionQueryKey)).not.toEqual(SESSION_RESPONSE));
  });

  it("shows the Órdenes placeholder and makes no request to a work-orders endpoint", async () => {
    // Defect this catches: a placeholder that still fetches, which would
    // 404 against a server that has not shipped work orders yet -- MSW's
    // onUnhandledFrame: "error" (test/server.ts) fails this test outright
    // on any request this test did not explicitly mock.
    mockSession();
    renderShell("/ordenes");

    expect(await screen.findByText("Próximamente")).toBeInTheDocument();
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
              <Route path="/ordenes" element={<WorkOrdersComingSoon />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await screen.findByText("Taller Ana");
    const user = userEvent.setup();
    await user.click(screen.getByRole("link", { name: "Órdenes" }));

    expect(await screen.findByText("Próximamente")).toBeInTheDocument();
  });
});

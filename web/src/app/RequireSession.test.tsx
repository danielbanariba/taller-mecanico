import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { sessionQueryKey } from "../features/auth/hooks";
import { server } from "../test/server";
import { renderWithQueryClient } from "../test/render";
import { RequireSession } from "./RequireSession";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

/** Like `renderGuarded`, but seeds the query cache with a session before mounting, simulating a cache restored from IndexedDB on reload. */
function renderGuardedWithCachedSession() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  queryClient.setQueryData(sessionQueryKey, SESSION);

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/inventario"]}>
        <Routes>
          <Route
            path="/inventario"
            element={
              <RequireSession>
                <div>Contenido protegido</div>
              </RequireSession>
            }
          />
          <Route path="/login" element={<div>Pantalla de inicio de sesión</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function renderGuarded() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/inventario"]}>
      <Routes>
        <Route
          path="/inventario"
          element={
            <RequireSession>
              <div>Contenido protegido</div>
            </RequireSession>
          }
        />
        <Route path="/login" element={<div>Pantalla de inicio de sesión</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RequireSession", () => {
  it("redirects to /login when GET /api/auth/me returns 401", async () => {
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json({ detail: "not_authenticated" }, { status: 401 })),
    );

    renderGuarded();

    expect(await screen.findByText("Pantalla de inicio de sesión")).toBeInTheDocument();
  });

  it("renders the protected page when GET /api/auth/me returns 200", async () => {
    server.use(
      http.get("/api/auth/me", () =>
        HttpResponse.json(
          {
            user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
            workshop: { id: "w1", name: "Taller Ana" },
          },
          { status: 200 },
        ),
      ),
    );

    renderGuarded();

    expect(await screen.findByText("Contenido protegido")).toBeInTheDocument();
  });

  it("keeps rendering the protected page when a cached session exists but the background refetch fails with network_error", async () => {
    // Defect this catches: treating every `isError` the same (the original
    // bug) would bounce an offline mechanic with a perfectly good cached
    // session to the login screen, even though nothing about their session
    // is actually invalid.
    let callCount = 0;
    server.use(
      http.get("/api/auth/me", () => {
        callCount += 1;
        return HttpResponse.error();
      }),
    );

    renderGuardedWithCachedSession();

    expect(screen.getByText("Contenido protegido")).toBeInTheDocument();
    await waitFor(() => expect(callCount).toBeGreaterThan(0));
    expect(screen.getByText("Contenido protegido")).toBeInTheDocument();
    expect(screen.queryByText("Pantalla de inicio de sesión")).not.toBeInTheDocument();
  });

  it("shows a 'sin conexión' screen, not the login form, when GET /api/auth/me fails with network_error and there is no cached session", async () => {
    // Defect this catches: without this branch, an offline user with no
    // cached session would be sent to the login screen and could fill in
    // and submit a form that can never succeed while offline.
    server.use(http.get("/api/auth/me", () => HttpResponse.error()));

    renderGuarded();

    expect(await screen.findByText("Sin conexión")).toBeInTheDocument();
    expect(screen.queryByText("Pantalla de inicio de sesión")).not.toBeInTheDocument();
  });
});

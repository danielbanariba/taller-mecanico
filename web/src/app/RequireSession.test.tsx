import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { onlineManager, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { sessionQueryKey, useSession } from "../features/auth/hooks";
import { server } from "../test/server";
import { renderWithQueryClient } from "../test/render";
import { AppProviders } from "./providers";
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

/** Exposes the session query's status so a test can tell when a failed refetch has landed in the cache. */
function SessionProbe() {
  const session = useSession();
  return <div data-session-status={session.status}>Contenido protegido</div>;
}

/**
 * Mounts the guard under the real `AppProviders` (IndexedDB persister,
 * dehydrate options, buster), so unmounting and mounting it again is a
 * page reload as far as the persisted query cache is concerned.
 */
function renderApp() {
  return render(
    <AppProviders>
      <MemoryRouter initialEntries={["/inventario"]}>
        <Routes>
          <Route
            path="/inventario"
            element={
              <RequireSession>
                <SessionProbe />
              </RequireSession>
            }
          />
          <Route path="/login" element={<div>Pantalla de inicio de sesión</div>} />
        </Routes>
      </MemoryRouter>
    </AppProviders>,
  );
}

afterEach(() => {
  Reflect.deleteProperty(window.navigator, "onLine");
});

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

  it("keeps the cached session usable across repeated reloads while GET /api/auth/me cannot reach the server", async () => {
    // Defect this catches (T8): the persister only kept queries whose
    // status was "success", so the first failed session check offline (or
    // on a connection that reports online but drops every request) erased
    // the cached session from IndexedDB while the open page kept working;
    // the next reload found no session and blocked the whole app on the
    // "Sin conexión" screen.
    server.use(http.get("/api/auth/me", () => HttpResponse.json(SESSION)));
    const online = renderApp();
    await screen.findByText("Contenido protegido");
    online.unmount();

    server.use(http.get("/api/auth/me", () => HttpResponse.error()));
    Object.defineProperty(window.navigator, "onLine", { value: false, configurable: true });

    const firstReload = renderApp();
    const content = await screen.findByText("Contenido protegido");
    await waitFor(() => expect(content).toHaveAttribute("data-session-status", "error"));
    firstReload.unmount();

    renderApp();

    expect(await screen.findByText("Contenido protegido")).toBeInTheDocument();
    expect(screen.getByText("Sin conexión. Los cambios se guardan en el teléfono.")).toBeInTheDocument();
    expect(screen.queryByText("Sin conexión")).not.toBeInTheDocument();
  });

  it("shows the 'sin conexión' screen instead of an endless spinner when the session check is paused offline with no cached session", async () => {
    // Defect this catches: once TanStack Query's onlineManager is offline
    // (the browser fired `offline`), the session query pauses instead of
    // failing, so it stays `pending` forever and the guard spun without end.
    server.use(http.get("/api/auth/me", () => HttpResponse.error()));
    onlineManager.setOnline(false);

    renderGuarded();

    expect(await screen.findByText("Sin conexión")).toBeInTheDocument();
  });

  it("renders the protected page when the session check is paused offline but a session is cached", async () => {
    // Defect this catches: checking for a paused session check before
    // checking for cached data would block an offline mechanic who has a
    // perfectly good cached session.
    server.use(http.get("/api/auth/me", () => HttpResponse.error()));
    onlineManager.setOnline(false);

    renderGuardedWithCachedSession();

    expect(screen.getByText("Contenido protegido")).toBeInTheDocument();
    expect(screen.queryByText("Sin conexión")).not.toBeInTheDocument();
  });

  it("redirects to /login when GET /api/auth/me returns 401 even though a session is cached", async () => {
    // Defect this catches: a cached session made the guard ignore a real
    // 401 (expired or revoked session), so the mechanic stayed in an app
    // where every request failed and queued movements could never flush.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json({ detail: "not_authenticated" }, { status: 401 })),
    );

    renderGuardedWithCachedSession();

    expect(await screen.findByText("Pantalla de inicio de sesión")).toBeInTheDocument();
  });
});

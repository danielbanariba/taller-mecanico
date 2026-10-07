import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import type { Me } from "../features/auth/api";
import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/auth/RegisterPage";
import type { ItemOut } from "../features/inventory/api";
import { InventoryPage } from "../features/inventory/InventoryPage";
import { idbPersister } from "../shared/offline/idbPersister";
import { server } from "../test/server";
import { AppProviders } from "./providers";
import { RequireSession } from "./RequireSession";

const WORKSHOP_A: Me = {
  user: { id: "ua", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "wa", name: "Taller Ana" },
};

const WORKSHOP_B: Me = {
  user: { id: "ub", full_name: "Beto Díaz", phone: "88887777", role: "owner" },
  workshop: { id: "wb", name: "Taller Beto" },
};

function item(id: string, name: string): ItemOut {
  return {
    id,
    name,
    category: null,
    unit: "unidad",
    min_stock: 0,
    sale_price_cents: null,
    notes: null,
    stock: 3,
    needs_review: false,
    is_low: false,
    archived_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

/**
 * The real `AppProviders` (IndexedDB persister included), so unmounting and
 * rendering again is a page reload as far as the persisted cache goes.
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
                <InventoryPage />
              </RequireSession>
            }
          />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/registro" element={<RegisterPage />} />
        </Routes>
      </MemoryRouter>
    </AppProviders>,
  );
}

async function persistedCacheText(): Promise<string> {
  return JSON.stringify((await idbPersister.restoreClient()) ?? null);
}

type User = ReturnType<typeof userEvent.setup>;

/** From the login screen, starts workshop B's session the way a mechanic would. */
const START_WORKSHOP_B_SESSION: Record<"login" | "register", (user: User) => Promise<void>> = {
  login: async (user) => {
    await user.type(await screen.findByLabelText(/teléfono/i), "88887777");
    await user.type(screen.getByLabelText(/contraseña/i), "password123");
    await user.click(screen.getByRole("button", { name: /iniciar sesión/i }));
  },
  register: async (user) => {
    await user.click(await screen.findByRole("link", { name: /regístrese/i }));
    await user.type(await screen.findByLabelText(/nombre del taller/i), "Taller Beto");
    await user.type(screen.getByLabelText(/nombre del propietario/i), "Beto Díaz");
    await user.type(screen.getByLabelText(/teléfono/i), "88887777");
    await user.type(screen.getByLabelText(/contraseña/i), "password123");
    await user.click(screen.getByRole("button", { name: /crear cuenta/i }));
  },
};

describe("switching workshops on one phone", () => {
  it.each(["login", "register"] as const)(
    "drops the previous workshop's cached inventory, on screen and in IndexedDB, when another workshop starts a session (%s)",
    async (flow) => {
      // Defect this catches (T9, seen in a real browser): login and register
      // never cleared the cache, so after workshop A's session expired and
      // workshop B logged in on the same phone, IndexedDB still held A's
      // inventory, ready to be shown to B.
      let session: Me | null = WORKSHOP_A;
      let releaseWorkshopBItems = () => {};
      const workshopBItemsReady = new Promise<void>((resolve) => {
        releaseWorkshopBItems = resolve;
      });
      server.use(
        http.get("/api/auth/me", () =>
          session ? HttpResponse.json(session) : HttpResponse.json({ detail: "not_authenticated" }, { status: 401 }),
        ),
        http.get("/api/inventory/items", async () => {
          if (session === null) {
            return HttpResponse.json({ detail: "not_authenticated" }, { status: 401 });
          }
          if (session === WORKSHOP_A) {
            return HttpResponse.json([item("a-1", "Filtro de Ana")]);
          }
          await workshopBItemsReady;
          return HttpResponse.json([item("b-1", "Bujía de Beto")]);
        }),
        http.post("/api/auth/login", () => {
          session = WORKSHOP_B;
          return HttpResponse.json(WORKSHOP_B);
        }),
        http.post("/api/auth/register", () => {
          session = WORKSHOP_B;
          return HttpResponse.json(WORKSHOP_B, { status: 201 });
        }),
      );

      const workshopAVisit = renderApp();
      await screen.findByText("Filtro de Ana");
      await waitFor(async () => expect(await persistedCacheText()).toContain("Filtro de Ana"));
      workshopAVisit.unmount();

      // Workshop A's session cookie expires; workshop B starts a session on
      // this phone.
      session = null;
      renderApp();
      await START_WORKSHOP_B_SESSION[flow](userEvent.setup());

      expect(await screen.findByRole("heading", { name: "Taller Beto" })).toBeInTheDocument();
      expect(screen.queryByText("Filtro de Ana")).not.toBeInTheDocument();
      await waitFor(async () => expect(await persistedCacheText()).not.toContain("Filtro de Ana"));

      releaseWorkshopBItems();
      expect(await screen.findByText("Bujía de Beto")).toBeInTheDocument();
    },
  );
});

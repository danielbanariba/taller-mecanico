import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { sessionQueryKey } from "../auth/hooks";
import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { vehicleQueryKey } from "./hooks";
import { VehicleDetailPage } from "./VehicleDetailPage";
import type { VehicleDetailOut } from "./api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

const VEHICLE: VehicleDetailOut = {
  id: "v1",
  customer_id: "c1",
  vehicle_type: "car",
  make: "Toyota",
  model: "Corolla",
  year: 2015,
  color: null,
  plate: "HAB1234",
  notes: null,
  archived_at: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  owner: {
    id: "c1",
    full_name: "María Hernández",
    phone: null,
    phone_is_mobile: null,
    notes: null,
    billing_name: null,
    rtn: null,
    archived_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
};

/**
 * Renders the page over a cache that already holds the session and the
 * vehicle -- what the persister restores from IndexedDB -- while every
 * request fails as it does without a connection.
 */
function renderDetailPageFromCacheWithoutConnection() {
  server.use(
    http.get("/api/auth/me", () => HttpResponse.error()),
    http.get("/api/vehicles/v1", () => HttpResponse.error()),
    http.get("/api/work-orders", () => HttpResponse.error()),
  );
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  queryClient.setQueryData(sessionQueryKey, SESSION);
  queryClient.setQueryData(vehicleQueryKey("w1", "v1"), VEHICLE);

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/clientes/c1/vehiculos/v1"]}>
        <Routes>
          <Route path="/clientes/:customerId/vehiculos/:vehicleId" element={<VehicleDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function orderSummary(number: number, status: string) {
  return {
    id: `o${number}`,
    number,
    status,
    vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
    customer: { id: "c1", full_name: "María Hernández" },
    total_cents: 10000,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

function renderVehicleDetailPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/clientes/c1/vehiculos/v1"]}>
      <Routes>
        <Route path="/clientes/:customerId/vehiculos/:vehicleId" element={<VehicleDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("VehicleDetailPage", () => {
  it("keeps showing the cached vehicle when refetching it fails for lack of connection", async () => {
    // Defect this catches: a failed refetch flips the vehicle query to
    // "error" while it still holds the cached vehicle; checking `isError`
    // (or the generic not-found branch) before the cached data would make
    // a previously visited vehicle disappear the moment the device goes
    // offline, instead of rendering what was already fetched.
    renderDetailPageFromCacheWithoutConnection();

    expect(await screen.findByRole("heading", { name: "Toyota Corolla" })).toBeInTheDocument();
    expect(screen.getByText(/HAB1234/)).toBeInTheDocument();
    expect(screen.queryByText("No se encontró el vehículo.")).not.toBeInTheDocument();
  });

  it("shows that vehicle's work orders, most recent first", async () => {
    // Defect this catches: a vehicle's service history missing from its
    // detail screen, filtered to the wrong vehicle, or reordered, would
    // leave a mechanic unable to tell what was last done to this vehicle
    // without hunting through the full Historial tab for its plate.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/vehicles/v1", () => HttpResponse.json(VEHICLE)),
      http.get("/api/work-orders", ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get("vehicle_id")).toBe("v1");
        return HttpResponse.json([orderSummary(2, "in_progress"), orderSummary(1, "completed")]);
      }),
    );
    renderVehicleDetailPage();

    const orderTitles = await screen.findAllByText(/^Orden #/);
    expect(orderTitles.map((element) => element.textContent)).toEqual(["Orden #2", "Orden #1"]);
  });
});

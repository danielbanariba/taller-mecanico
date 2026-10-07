import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { NewVehiclePage } from "./NewVehiclePage";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

// `NewVehiclePage` reads `useWorkshopId()` (for the create mutation's
// query key), which fires a real `GET /api/auth/me` if nothing mocks it --
// every test in this file needs the session, not just the ones that
// assert on it.
beforeEach(() => {
  server.use(http.get("/api/auth/me", () => HttpResponse.json(SESSION)));
});

function renderNewVehiclePage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/clientes/c1/vehiculos/nuevo"]}>
      <Routes>
        <Route path="/clientes/:customerId/vehiculos/nuevo" element={<NewVehiclePage />} />
        <Route path="/clientes/:customerId" element={<div>Detalle de cliente</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function vehicleResponse(id: string) {
  return {
    id,
    customer_id: "c1",
    vehicle_type: "car",
    make: "Toyota",
    model: null,
    year: null,
    color: null,
    plate: null,
    notes: null,
    archived_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

describe("NewVehiclePage", () => {
  it("reuses the same client-generated id across a failed submit and its retry", async () => {
    // Defect this catches: generating a new client id per submit attempt
    // (instead of once per form mount) would turn a retry after a failed
    // request into a second, distinct vehicle instead of an idempotent
    // replay of the same one.
    const capturedIds: string[] = [];
    let shouldFail = true;
    server.use(
      http.post("/api/vehicles", async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        capturedIds.push(body.id as string);
        if (shouldFail) {
          shouldFail = false;
          return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
        }
        return HttpResponse.json(vehicleResponse(body.id as string), { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderNewVehiclePage();

    await user.type(screen.getByLabelText(/marca/i), "Toyota");
    await user.click(screen.getByRole("button", { name: /guardar vehículo/i }));
    await screen.findByText("Ocurrió un error. Intente de nuevo.");
    await user.click(screen.getByRole("button", { name: /guardar vehículo/i }));

    expect(await screen.findByText("Detalle de cliente")).toBeInTheDocument();
    expect(capturedIds).toHaveLength(2);
    expect(capturedIds[0]).toBe(capturedIds[1]);
    expect(capturedIds[0]).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
  });

  it("shows the Spanish message for invalid_plate on a 422, not the generic fallback", async () => {
    // Defect this catches: a vehicle-specific error code added to the API
    // falling through copy.ts's shared map to the generic message instead
    // of its own Spanish text.
    server.use(http.post("/api/vehicles", () => HttpResponse.json({ detail: "invalid_plate" }, { status: 422 })));
    const user = userEvent.setup();
    renderNewVehiclePage();

    await user.type(screen.getByLabelText(/marca/i), "Toyota");
    await user.click(screen.getByRole("button", { name: /guardar vehículo/i }));

    expect(await screen.findByText("La placa no es válida.")).toBeInTheDocument();
  });

  it("shows the Spanish message for plate_taken on a 409, not the generic fallback", async () => {
    // Defect this catches: a duplicate-plate conflict falling through to
    // the generic error message instead of explaining the actual reason
    // the save failed.
    server.use(http.post("/api/vehicles", () => HttpResponse.json({ detail: "plate_taken" }, { status: 409 })));
    const user = userEvent.setup();
    renderNewVehiclePage();

    await user.type(screen.getByLabelText(/marca/i), "Toyota");
    await user.click(screen.getByRole("button", { name: /guardar vehículo/i }));

    expect(await screen.findByText("Ya existe un vehículo activo con esa placa.")).toBeInTheDocument();
  });

  it("disables submission and explains why when offline, without calling the API", async () => {
    // Defect this catches: creating a vehicle has no client-generated-id
    // conflict recovery for a server round trip that can never happen
    // offline in this MVP, so letting the form submit anyway would just
    // hang on a network_error with no clear explanation.
    //
    // This runs last in the file on purpose, mirroring
    // `NewCustomerPage.test.tsx`: jsdom's `navigator.onLine` is an
    // inherited prototype property, so the usual save/restore guard has
    // nothing to restore and the override below outlives this test
    // regardless.
    let apiWasCalled = false;
    server.use(
      http.post("/api/vehicles", () => {
        apiWasCalled = true;
        return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
      }),
    );
    Object.defineProperty(window.navigator, "onLine", { value: false, configurable: true });

    const user = userEvent.setup();
    renderNewVehiclePage();

    await user.type(screen.getByLabelText(/marca/i), "Toyota");
    expect(screen.getByText("Conéctese a internet para agregar vehículos.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /guardar vehículo/i })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: /guardar vehículo/i }));
    expect(apiWasCalled).toBe(false);
  });
});

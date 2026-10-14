import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { EditVehiclePage } from "./EditVehiclePage";
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

function renderEditVehiclePage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/clientes/c1/vehiculos/v1/editar"]}>
      <Routes>
        <Route path="/clientes/:customerId/vehiculos/:vehicleId/editar" element={<EditVehiclePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("EditVehiclePage", () => {
  it("has a back link to the vehicle's own detail screen", async () => {
    // Defect this catches: this edit screen has no way back except the
    // bottom nav (a QA sweep finding); a link whose `to` drifts from the
    // vehicle it is actually editing would strand the mechanic on the
    // wrong vehicle's detail screen, or a nonexistent route.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/vehicles/v1", () => HttpResponse.json(VEHICLE)),
    );
    renderEditVehiclePage();

    expect(await screen.findByRole("link", { name: "Volver al vehículo" })).toHaveAttribute(
      "href",
      "/clientes/c1/vehiculos/v1",
    );
  });
});

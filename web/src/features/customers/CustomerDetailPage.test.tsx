import { describe, expect, it } from "vitest";
import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { CustomerDetailPage } from "./CustomerDetailPage";
import type { CustomerOut, VehicleOut } from "./api";

const SESSION_RESPONSE = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

const CUSTOMER: CustomerOut = {
  id: "c1",
  full_name: "María Hernández",
  phone: "98765432",
  phone_is_mobile: true,
  notes: null,
  archived_at: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function vehicle(id: string, make: string, plate: string | null): VehicleOut {
  return {
    id,
    customer_id: "c1",
    vehicle_type: "car",
    make,
    model: null,
    year: null,
    color: null,
    plate,
    notes: null,
    archived_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

const ORDER_SUMMARY = {
  id: "order-1",
  number: 7,
  status: "quote",
  vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
  customer: { id: "c1", full_name: "María Hernández" },
  total_cents: 50000,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function renderCustomerDetailPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/clientes/c1"]}>
      <Routes>
        <Route path="/clientes/:customerId" element={<CustomerDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("CustomerDetailPage", () => {
  it("lists that customer's active vehicles", async () => {
    // Defect this catches: fetching every vehicle in the workshop (or a
    // different customer's) instead of scoping the request to this
    // customer's own `GET /customers/{id}/vehicles`, which would either
    // show the wrong vehicles or none at all.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION_RESPONSE)),
      http.get("/api/customers/c1", () => HttpResponse.json(CUSTOMER)),
      http.get("/api/customers/c1/vehicles", () =>
        HttpResponse.json([vehicle("v1", "Toyota", "HAB1234"), vehicle("v2", "Honda", null)]),
      ),
      // `CustomerDetailPage` also renders this customer's orders
      // unconditionally (`useWorkOrdersForCustomer`); left unmocked, the
      // request errors silently and the section would pass this test
      // empty without anyone noticing.
      http.get("/api/work-orders", () => HttpResponse.json([ORDER_SUMMARY])),
    );
    renderCustomerDetailPage();

    expect(await screen.findByText("Toyota")).toBeInTheDocument();
    const vehiclesSection = screen.getByRole("heading", { name: "Vehículos" }).closest("section");
    if (!vehiclesSection) throw new Error("vehicles section not found");
    expect(within(vehiclesSection).getByText("Honda")).toBeInTheDocument();
    expect(within(vehiclesSection).getByText(/HAB1234/)).toBeInTheDocument();
    // Defect this catches: the orders section wiring itself (the query,
    // its key, or `WorkOrderList`'s render) silently showing nothing for
    // this customer's own work orders.
    expect(await screen.findByText("Orden #7")).toBeInTheDocument();
  });
});

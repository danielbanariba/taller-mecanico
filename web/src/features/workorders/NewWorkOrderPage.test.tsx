import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { NewWorkOrderPage } from "./NewWorkOrderPage";
import type { WorkOrderOut } from "./api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

function orderResponse(id: string, vehicleId: string): WorkOrderOut {
  return {
    id,
    number: 1,
    status: "quote",
    allowed_transitions: ["approved", "cancelled"],
    lines_editable: true,
    vehicle: { id: vehicleId, vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
    customer: { id: "c1", full_name: "María Hernández", phone: "98765432", phone_is_mobile: true },
    complaint: null,
    odometer_km: null,
    notes: null,
    lines: [],
    total_cents: 0,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    approved_at: null,
    started_at: null,
    completed_at: null,
    delivered_at: null,
    cancelled_at: null,
  };
}

/** Customer search needs a resolved session (`useCustomers`/`useVehiclesForCustomer` are both `enabled: workshopId !== undefined`), unlike the customer/vehicle create screens this flow otherwise mirrors. */
function mockSessionCustomerAndVehicle() {
  server.use(
    http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
    http.get("/api/customers", () =>
      HttpResponse.json([
        {
          id: "c1",
          full_name: "María Hernández",
          phone: "98765432",
          phone_is_mobile: true,
          notes: null,
          archived_at: null,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        },
      ]),
    ),
    http.get("/api/customers/c1/vehicles", () =>
      HttpResponse.json([
        {
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
        },
      ]),
    ),
  );
}

function renderNewWorkOrderPage(initialEntry: string = "/ordenes/nueva") {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/ordenes/nueva" element={<NewWorkOrderPage />} />
        <Route path="/ordenes/:orderId" element={<div>Detalle de orden</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function vehicleWithOwnerResponse() {
  return {
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
      phone: "98765432",
      phone_is_mobile: true,
      notes: null,
      archived_at: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  };
}

async function pickCustomerAndVehicle(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByText("María Hernández"));
  await user.click(await screen.findByText("Toyota Corolla"));
}

describe("NewWorkOrderPage", () => {
  it("reuses the same client-generated id across a failed submit and its retry", async () => {
    // Defect this catches: generating a new client id per submit attempt
    // (instead of once per form mount) would turn a retry after a failed
    // create into a second, distinct work order -- burning a second number
    // instead of replaying the first (the `work-orders` spec's numbering
    // guarantee).
    const capturedIds: string[] = [];
    let shouldFail = true;
    mockSessionCustomerAndVehicle();
    server.use(
      http.post("/api/work-orders", async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        capturedIds.push(body.id as string);
        if (shouldFail) {
          shouldFail = false;
          return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
        }
        return HttpResponse.json(orderResponse(body.id as string, body.vehicle_id as string), { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderNewWorkOrderPage();

    await pickCustomerAndVehicle(user);
    await user.click(screen.getByRole("button", { name: /crear orden/i }));
    await screen.findByText("Ocurrió un error. Intente de nuevo.");
    await user.click(screen.getByRole("button", { name: /crear orden/i }));

    expect(await screen.findByText("Detalle de orden")).toBeInTheDocument();
    expect(capturedIds).toHaveLength(2);
    expect(capturedIds[0]).toBe(capturedIds[1]);
    expect(capturedIds[0]).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
  });

  it("skips the customer and vehicle pickers when opened with a ?vehiculo= preselection", async () => {
    // Defect this catches: the vehicle detail screen's "Nueva orden" action
    // links to `/ordenes/nueva?vehiculo=<id>` precisely so the mechanic
    // never has to re-search for the customer and vehicle they just came
    // from. Without reading the query param, this screen would always
    // start at the customer search step and ignore which vehicle it was
    // opened for.
    //
    // Must run before "disables creation ..." below: that test overrides
    // `navigator.onLine` with no restore (see its own comment), and this
    // one needs the default online state to submit.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/vehicles/v1", () => HttpResponse.json(vehicleWithOwnerResponse())),
      // `useCustomers` fires in the background regardless of which step is
      // shown (its `enabled` only checks the session, not the step), so an
      // unmocked request here would fail under MSW's `onUnhandledFrame`.
      http.get("/api/customers", () => HttpResponse.json([])),
      http.post("/api/work-orders", async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(orderResponse(body.id as string, body.vehicle_id as string), { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderNewWorkOrderPage("/ordenes/nueva?vehiculo=v1");

    expect(await screen.findByText("María Hernández")).toBeInTheDocument();
    expect(screen.getByText(/Toyota Corolla/)).toBeInTheDocument();
    expect(screen.queryByText(/buscar cliente/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /cambiar vehículo/i })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /crear orden/i }));
    expect(await screen.findByText("Detalle de orden")).toBeInTheDocument();
  });

  it("disables creation and explains why when offline, without calling the API", async () => {
    // Defect this catches: creating a work order has no client-generated-id
    // conflict recovery for a server round trip that can never happen
    // offline in this MVP (AD-17), so letting the confirm step submit
    // anyway would just hang on a network_error with no clear explanation.
    //
    // This runs last in the file on purpose, mirroring
    // `NewCustomerPage.test.tsx`: jsdom's `navigator.onLine` is an
    // inherited prototype property, so the usual save/restore guard has
    // nothing to restore and the override below outlives this test
    // regardless.
    let apiWasCalled = false;
    mockSessionCustomerAndVehicle();
    server.use(
      http.post("/api/work-orders", () => {
        apiWasCalled = true;
        return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
      }),
    );
    Object.defineProperty(window.navigator, "onLine", { value: false, configurable: true });

    const user = userEvent.setup();
    renderNewWorkOrderPage();

    await pickCustomerAndVehicle(user);
    expect(screen.getByText("Conéctese a internet para crear órdenes.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /crear orden/i })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: /crear orden/i }));
    expect(apiWasCalled).toBe(false);
  });
});

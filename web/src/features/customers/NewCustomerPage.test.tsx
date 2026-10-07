import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { NewCustomerPage } from "./NewCustomerPage";

function renderNewCustomerPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/clientes/nuevo"]}>
      <Routes>
        <Route path="/clientes/nuevo" element={<NewCustomerPage />} />
        <Route path="/clientes" element={<div>Lista de clientes</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function customerResponse(id: string, fullName: string) {
  return {
    id,
    full_name: fullName,
    phone: null,
    phone_is_mobile: null,
    notes: null,
    archived_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

describe("NewCustomerPage", () => {
  it("reuses the same client-generated id across a failed submit and its retry", async () => {
    // Defect this catches: generating a new client id per submit attempt
    // (instead of once per form mount) would turn a retry after a failed
    // request into a second, distinct customer instead of an idempotent
    // replay of the same one.
    const capturedIds: string[] = [];
    let shouldFail = true;
    server.use(
      http.post("/api/customers", async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        capturedIds.push(body.id as string);
        if (shouldFail) {
          shouldFail = false;
          return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
        }
        return HttpResponse.json(customerResponse(body.id as string, body.full_name as string), { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderNewCustomerPage();

    await user.type(screen.getByLabelText(/nombre completo/i), "María Hernández");
    await user.click(screen.getByRole("button", { name: /guardar cliente/i }));
    await screen.findByText("Ocurrió un error. Intente de nuevo.");
    await user.click(screen.getByRole("button", { name: /guardar cliente/i }));

    expect(await screen.findByText("Lista de clientes")).toBeInTheDocument();
    expect(capturedIds).toHaveLength(2);
    expect(capturedIds[0]).toBe(capturedIds[1]);
    expect(capturedIds[0]).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
  });

  it("shows the Spanish message for invalid_phone on a 422, not the generic fallback", async () => {
    // Defect this catches: a new error code added to the API falling
    // through copy.ts's map to the generic message instead of its own
    // Spanish text.
    server.use(http.post("/api/customers", () => HttpResponse.json({ detail: "invalid_phone" }, { status: 422 })));
    const user = userEvent.setup();
    renderNewCustomerPage();

    await user.type(screen.getByLabelText(/nombre completo/i), "María Hernández");
    await user.click(screen.getByRole("button", { name: /guardar cliente/i }));

    expect(
      await screen.findByText("El teléfono no es válido. Use un número hondureño de 8 dígitos."),
    ).toBeInTheDocument();
  });

  it("shows the Spanish message for plate_taken on a 409, not the generic fallback", async () => {
    // Defect this catches: copy.ts's error-code map is shared by customers
    // and (from Slice 5) vehicles -- a missing plate_taken entry would
    // make a vehicle-side conflict fall through to the generic message
    // instead of its own Spanish text. This exercises that shared map
    // through the customer form now, ahead of the vehicle screens that
    // trigger it for real.
    server.use(http.post("/api/customers", () => HttpResponse.json({ detail: "plate_taken" }, { status: 409 })));
    const user = userEvent.setup();
    renderNewCustomerPage();

    await user.type(screen.getByLabelText(/nombre completo/i), "María Hernández");
    await user.click(screen.getByRole("button", { name: /guardar cliente/i }));

    expect(await screen.findByText("Ya existe un vehículo activo con esa placa.")).toBeInTheDocument();
  });

  it("disables submission and explains why when offline, without calling the API", async () => {
    // Defect this catches: creating a customer has no client-generated-id
    // conflict recovery for a server round trip that can never happen
    // offline in this MVP, so letting the form submit anyway would just
    // hang on a network_error with no clear explanation.
    //
    // This runs last in the file on purpose, mirroring
    // `NewItemPage.test.tsx`: jsdom's `navigator.onLine` is an inherited
    // prototype property, so `getOwnPropertyDescriptor` on the instance
    // returns undefined and the usual save/restore guard has nothing to
    // restore -- the override below outlives this test regardless.
    let apiWasCalled = false;
    server.use(
      http.post("/api/customers", () => {
        apiWasCalled = true;
        return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
      }),
    );
    Object.defineProperty(window.navigator, "onLine", { value: false, configurable: true });

    const user = userEvent.setup();
    renderNewCustomerPage();

    await user.type(screen.getByLabelText(/nombre completo/i), "María Hernández");
    expect(screen.getByText("Conéctese a internet para agregar clientes.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /guardar cliente/i })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: /guardar cliente/i }));
    expect(apiWasCalled).toBe(false);
  });
});

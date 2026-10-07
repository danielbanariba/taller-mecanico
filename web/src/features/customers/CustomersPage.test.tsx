import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { CustomersPage } from "./CustomersPage";
import type { CustomerOut } from "./api";

function customer(id: string, fullName: string): CustomerOut {
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

function renderCustomersPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/clientes"]}>
      <Routes>
        <Route path="/clientes" element={<CustomersPage />} />
        <Route path="/clientes/nuevo" element={<div>Nuevo cliente</div>} />
        <Route path="/clientes/:customerId/editar" element={<div>Editar cliente</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

const SESSION_RESPONSE = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

describe("CustomersPage", () => {
  it("renders a customer whose accented name was found by an unaccented search", async () => {
    // Defect this catches: the search input losing its typed, debounced
    // value on the way to the request's `q` parameter, which would leave
    // "María" out of a list searched for "maria" even though the API
    // itself matches accent-insensitively.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION_RESPONSE)),
      http.get("/api/customers", ({ request }) => {
        const url = new URL(request.url);
        const q = url.searchParams.get("q");
        return HttpResponse.json(q === "maria" ? [customer("c1", "María Hernández")] : []);
      }),
    );
    const user = userEvent.setup();
    renderCustomersPage();

    await user.type(screen.getByLabelText(/buscar cliente/i), "maria");

    expect(await screen.findByText("María Hernández")).toBeInTheDocument();
  });
});

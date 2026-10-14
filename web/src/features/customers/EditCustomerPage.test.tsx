import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { EditCustomerPage } from "./EditCustomerPage";
import type { CustomerOut } from "./api";

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
  billing_name: null,
  rtn: null,
  archived_at: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function renderEditCustomerPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/clientes/c1/editar"]}>
      <Routes>
        <Route path="/clientes/:customerId/editar" element={<EditCustomerPage />} />
        <Route path="/clientes" element={<div>Lista de clientes</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("EditCustomerPage", () => {
  it("shows the archived notice instead of the edit form when reached for an archived customer", async () => {
    // Defect this catches: a direct link to an archived customer's
    // "Editar cliente" (e.g. a stale bookmark, or a link clicked right
    // before the customer was archived elsewhere) rendering a working
    // form that silently renames the archived record, instead of this
    // screen refusing the edit up front the way the API itself does
    // (`customer_archived`).
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION_RESPONSE)),
      http.get("/api/customers/c1", () =>
        HttpResponse.json({ ...CUSTOMER, archived_at: "2026-02-01T00:00:00Z" }),
      ),
    );
    renderEditCustomerPage();

    expect(await screen.findByText(/archivado/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/nombre completo/i)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Volver a clientes" })).toHaveAttribute("href", "/clientes");
  });
});

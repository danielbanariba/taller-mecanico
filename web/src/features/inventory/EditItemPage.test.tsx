import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { server } from "../../test/server";
import { renderWithQueryClient } from "../../test/render";
import { EditItemPage } from "./EditItemPage";

function renderEditPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/inventario/item-1/editar"]}>
      <Routes>
        <Route path="/inventario/:id/editar" element={<EditItemPage />} />
        <Route path="/inventario" element={<div>Pantalla de inventario</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("EditItemPage", () => {
  it("shows the Spanish not-found message with a way back to the list for a 404", async () => {
    // Defect this catches: the not-found state had no way back to the
    // list, leaving the mechanic stuck on a dead-end screen (the detail
    // page already got one in T5b).
    server.use(
      http.get("/api/auth/me", () =>
        HttpResponse.json({
          user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
          workshop: { id: "w1", name: "Taller Ana" },
        }),
      ),
    );
    server.use(
      http.get("/api/inventory/items/item-1", () =>
        HttpResponse.json({ detail: "item_not_found" }, { status: 404 }),
      ),
    );
    server.use(http.get("/api/inventory/items", () => HttpResponse.json([])));

    renderEditPage();

    expect(await screen.findByText("No se encontró el repuesto.")).toBeInTheDocument();
    const backLink = screen.getByRole("link", { name: /volver al inventario/i });
    expect(backLink).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(backLink);
    expect(await screen.findByText("Pantalla de inventario")).toBeInTheDocument();
  });
});

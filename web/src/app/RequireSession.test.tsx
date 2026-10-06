import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { server } from "../test/server";
import { renderWithQueryClient } from "../test/render";
import { RequireSession } from "./RequireSession";

function renderGuarded() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/inventario"]}>
      <Routes>
        <Route
          path="/inventario"
          element={
            <RequireSession>
              <div>Contenido protegido</div>
            </RequireSession>
          }
        />
        <Route path="/login" element={<div>Pantalla de inicio de sesión</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RequireSession", () => {
  it("redirects to /login when GET /api/auth/me returns 401", async () => {
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json({ detail: "not_authenticated" }, { status: 401 })),
    );

    renderGuarded();

    expect(await screen.findByText("Pantalla de inicio de sesión")).toBeInTheDocument();
  });

  it("renders the protected page when GET /api/auth/me returns 200", async () => {
    server.use(
      http.get("/api/auth/me", () =>
        HttpResponse.json(
          {
            user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
            workshop: { id: "w1", name: "Taller Ana" },
          },
          { status: 200 },
        ),
      ),
    );

    renderGuarded();

    expect(await screen.findByText("Contenido protegido")).toBeInTheDocument();
  });
});

import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../../test/render";
import { server } from "../../../test/server";
import { FiscalProfilePage } from "./FiscalProfilePage";
import type { InvoicingSettingsOut } from "../api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

function settingsWithProfile(): InvoicingSettingsOut {
  return {
    profile: {
      rtn: "08011990123456",
      legal_name: "Taller Ana S. de R.L.",
      trade_name: "Taller Ana",
      address: "Col. Kennedy",
      phone: "22000000",
      email: "demo@example.invalid",
      establishment_code: "001",
      emission_point_code: "001",
      updated_at: "2026-01-01T00:00:00Z",
    },
    codes_locked: false,
    ranges: [],
    documents: [],
  };
}

function emptySettings(): InvoicingSettingsOut {
  return { profile: null, codes_locked: false, ranges: [], documents: [] };
}

function renderPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/ordenes/facturacion/datos"]}>
      <Routes>
        <Route path="/ordenes/facturacion/datos" element={<FiscalProfilePage />} />
        <Route path="/ordenes/facturacion" element={<div>Pantalla de facturación</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("FiscalProfilePage", () => {
  it("prefills the form from the existing profile", async () => {
    // Defect this catches: the container never actually mapping the
    // fetched profile's snake_case fields onto the form's own value
    // shape, which would silently present an empty form to a workshop
    // that already configured its fiscal data.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/settings", () => HttpResponse.json(settingsWithProfile())),
    );
    renderPage();

    expect(await screen.findByLabelText(/razón social/i)).toHaveValue("Taller Ana S. de R.L.");
    expect(screen.getByLabelText(/^RTN$/i)).toHaveValue("08011990123456");
    expect(screen.getByLabelText(/código de establecimiento/i)).toHaveValue("001");
  });

  it("shows the Spanish message for invalid_establishment_code on a 422, not the generic fallback", async () => {
    // Defect this catches: a new error code falling through copy.ts's
    // map to the generic message instead of its own Spanish text.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/settings", () => HttpResponse.json(emptySettings())),
      http.put("/api/invoicing/profile", () =>
        HttpResponse.json({ detail: "invalid_establishment_code" }, { status: 422 }),
      ),
    );
    const user = userEvent.setup();
    renderPage();

    await user.type(await screen.findByLabelText(/razón social/i), "Taller Ana S. de R.L.");
    await user.type(screen.getByLabelText(/nombre comercial/i), "Taller Ana");
    await user.type(screen.getByLabelText(/^RTN$/i), "08011990123456");
    await user.type(screen.getByLabelText(/dirección/i), "Col. Kennedy");
    await user.type(screen.getByLabelText(/teléfono/i), "22000000");
    await user.type(screen.getByLabelText(/correo electrónico/i), "demo@example.invalid");
    await user.type(screen.getByLabelText(/código de establecimiento/i), "9");
    await user.type(screen.getByLabelText(/código de punto de emisión/i), "001");
    await user.click(screen.getByRole("button", { name: /guardar datos fiscales/i }));

    expect(
      await screen.findByText("El código de establecimiento debe tener exactamente 3 dígitos."),
    ).toBeInTheDocument();
  });
});

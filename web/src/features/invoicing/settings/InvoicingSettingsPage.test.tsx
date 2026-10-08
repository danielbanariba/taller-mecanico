import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { onlineManager } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../../test/render";
import { server } from "../../../test/server";
import { InvoicingSettingsPage } from "./InvoicingSettingsPage";
import type { CaiRangeOut, InvoicingSettingsOut } from "../api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

function settingsResponse(overrides: Partial<InvoicingSettingsOut> = {}): InvoicingSettingsOut {
  return {
    profile: null,
    codes_locked: false,
    ranges: [],
    documents: [
      {
        document_type: "01",
        ready: false,
        blocked_reason: "fiscal_profile_missing",
        active_range_id: null,
        next_number: null,
      },
    ],
    ...overrides,
  };
}

function range(id: string, state: CaiRangeOut["state"]): CaiRangeOut {
  return {
    id,
    document_type: "01",
    cai: "ABCDEFGHIJ1234567890",
    establishment_code: "001",
    emission_point_code: "001",
    range_start: 1,
    range_end: 100,
    next_number: 1,
    remaining: 100,
    first_number: "001-001-01-00000001",
    last_number: "001-001-01-00000100",
    issue_deadline: "2027-01-01",
    state,
    in_use: false,
    created_at: "2026-01-01T00:00:00Z",
  };
}

function renderSettingsPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/ordenes/facturacion"]}>
      <Routes>
        <Route path="/ordenes/facturacion" element={<InvoicingSettingsPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("InvoicingSettingsPage", () => {
  it("shows the SAR/contador/thermal-paper notice with a 'Configurar' action when no profile exists", async () => {
    // Defect this catches: the opt-in path staying unclear with no
    // profile, because the notice (or the way to start configuring one)
    // never renders until a profile already exists.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/settings", () => HttpResponse.json(settingsResponse())),
    );
    renderSettingsPage();

    expect(await screen.findByText(/registre este sistema ante la sar/i)).toBeInTheDocument();
    expect(screen.getByText(/confirme este módulo con su contador/i)).toBeInTheDocument();
    expect(screen.getByText(/papel certificado/i)).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Configurar" })).toBeInTheDocument();
  });

  it("still shows the same notices once the profile is complete", async () => {
    // Defect this catches: the notice disappearing once it is least
    // needed -- right after the workshop finishes configuring -- instead
    // of staying visible for as long as real documents are unconfirmed.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/settings", () =>
        HttpResponse.json(
          settingsResponse({
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
            documents: [
              {
                document_type: "01",
                ready: false,
                blocked_reason: "cai_range_missing",
                active_range_id: null,
                next_number: null,
              },
            ],
          }),
        ),
      ),
    );
    renderSettingsPage();

    expect(await screen.findByText(/registre este sistema ante la sar/i)).toBeInTheDocument();
    expect(screen.getByText(/confirme este módulo con su contador/i)).toBeInTheDocument();
    expect(screen.getByText(/papel certificado/i)).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Editar datos fiscales" })).toBeInTheDocument();
  });

  it("renders a distinct Spanish message for each blocked_reason", async () => {
    // Defect this catches: every blocked reason rendering the same
    // generic text, leaving the owner no idea what to do next.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/settings", () =>
        HttpResponse.json(
          settingsResponse({
            documents: [
              {
                document_type: "01",
                ready: false,
                blocked_reason: "cai_range_expired",
                active_range_id: null,
                next_number: null,
              },
            ],
          }),
        ),
      ),
    );
    renderSettingsPage();

    expect(await screen.findByText("El rango de CAI venció. Registre uno nuevo.")).toBeInTheDocument();
  });

  it("renders a distinct label for each CAI range state", async () => {
    // Defect this catches: a blocked state (exhausted/expired) shown as
    // though it were still usable, or every state rendering one label.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/settings", () =>
        HttpResponse.json(
          settingsResponse({
            ranges: [range("r1", "active"), range("r2", "standby"), range("r3", "exhausted"), range("r4", "expired")],
          }),
        ),
      ),
    );
    renderSettingsPage();

    expect(await screen.findByText("Activo")).toBeInTheDocument();
    expect(screen.getByText("En espera")).toBeInTheDocument();
    expect(screen.getByText("Agotado")).toBeInTheDocument();
    expect(screen.getByText("Vencido")).toBeInTheDocument();
  });

  it("disables the profile and range actions while offline, with the Spanish message", async () => {
    // Defect this catches: a write attempted (or silently allowed)
    // offline, when the API it needs is unreachable anyway.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/settings", () => HttpResponse.json(settingsResponse())),
    );
    renderSettingsPage();
    await screen.findByRole("button", { name: "Configurar" });
    onlineManager.setOnline(false);

    expect(await screen.findByText("Conéctese a internet para guardar los datos fiscales.")).toBeInTheDocument();
    expect(screen.getByText("Conéctese a internet para registrar o editar un rango de CAI.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Configurar" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Registrar rango" })).toBeDisabled();
  });
});

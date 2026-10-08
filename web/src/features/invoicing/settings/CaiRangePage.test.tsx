import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../../test/render";
import { server } from "../../../test/server";
import { CaiRangePage } from "./CaiRangePage";
import type { CaiRangeOut, InvoicingSettingsOut } from "../api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

function emptySettings(): InvoicingSettingsOut {
  return {
    profile: null,
    codes_locked: false,
    ranges: [],
    documents: [
      { document_type: "01", ready: false, blocked_reason: "fiscal_profile_missing", active_range_id: null, next_number: null },
    ],
  };
}

function range(overrides: Partial<CaiRangeOut> = {}): CaiRangeOut {
  return {
    id: "r1",
    document_type: "01",
    cai: "ABCDEFGHIJ1234567890",
    establishment_code: "001",
    emission_point_code: "001",
    range_start: 1,
    range_end: 500,
    next_number: 5,
    remaining: 496,
    first_number: "001-001-01-00000001",
    last_number: "001-001-01-00000500",
    issue_deadline: "2027-01-01",
    state: "active",
    in_use: true,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderCreatePage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/ordenes/facturacion/rangos/nuevo"]}>
      <Routes>
        <Route path="/ordenes/facturacion/rangos/nuevo" element={<CaiRangePage />} />
        <Route path="/ordenes/facturacion" element={<div>Pantalla de facturación</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function renderEditPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/ordenes/facturacion/rangos/r1"]}>
      <Routes>
        <Route path="/ordenes/facturacion/rangos/:rangeId" element={<CaiRangePage />} />
        <Route path="/ordenes/facturacion" element={<div>Pantalla de facturación</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

async function fillValidRange(user: ReturnType<typeof userEvent.setup>) {
  await user.type(await screen.findByLabelText(/^CAI$/i), "ABCDEFGHIJ1234567890");
  await user.type(screen.getByLabelText(/número inicial/i), "1");
  await user.type(screen.getByLabelText(/número final/i), "500");
  await user.type(screen.getByLabelText(/fecha límite/i), "2027-01-01");
}

describe("CaiRangePage", () => {
  it("reuses the same client-generated id across a failed submit and its retry", async () => {
    // Defect this catches: generating a new client id per submit attempt
    // (instead of once per page mount) would turn a retry after a failed
    // request into a second, distinct CAI range registration instead of
    // an idempotent replay of the same one (`cai-ranges` spec).
    const capturedIds: string[] = [];
    let shouldFail = true;
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/settings", () => HttpResponse.json(emptySettings())),
      http.post("/api/invoicing/cai-ranges", async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        capturedIds.push(body.id as string);
        if (shouldFail) {
          shouldFail = false;
          return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
        }
        return HttpResponse.json(range({ id: body.id as string, in_use: false }), { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderCreatePage();

    await fillValidRange(user);
    await user.click(screen.getByRole("button", { name: /guardar rango/i }));
    await screen.findByText("Ocurrió un error. Intente de nuevo.");
    await user.click(screen.getByRole("button", { name: /guardar rango/i }));

    expect(await screen.findByText("Pantalla de facturación")).toBeInTheDocument();
    expect(capturedIds).toHaveLength(2);
    expect(capturedIds[0]).toBe(capturedIds[1]);
  });

  it("shows the Spanish message for cai_range_overlap on a 409, not the generic fallback", async () => {
    // Defect this catches: a new error code falling through copy.ts's
    // map to the generic message instead of its own Spanish text.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/settings", () => HttpResponse.json(emptySettings())),
      http.post("/api/invoicing/cai-ranges", () =>
        HttpResponse.json({ detail: "cai_range_overlap" }, { status: 409 }),
      ),
    );
    const user = userEvent.setup();
    renderCreatePage();

    await fillValidRange(user);
    await user.click(screen.getByRole("button", { name: /guardar rango/i }));

    expect(await screen.findByText("Ese rango se traslapa con uno que ya existe.")).toBeInTheDocument();
  });

  it("shows the Spanish message for cai_deadline_too_far on a 422, not the generic fallback", async () => {
    // Defect this catches: a new error code falling through copy.ts's
    // map to the generic message instead of its own Spanish text.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/settings", () => HttpResponse.json(emptySettings())),
      http.post("/api/invoicing/cai-ranges", () =>
        HttpResponse.json({ detail: "cai_deadline_too_far" }, { status: 422 }),
      ),
    );
    const user = userEvent.setup();
    renderCreatePage();

    await fillValidRange(user);
    await user.click(screen.getByRole("button", { name: /guardar rango/i }));

    expect(await screen.findByText("La fecha límite no puede ser mayor a un año.")).toBeInTheDocument();
  });

  it("disables every field when editing a range that already has documents issued", async () => {
    // Defect this catches: the container never actually passing the
    // fetched range's own `in_use` flag through to the form, which would
    // let a used range's bounds be edited into a silent 409 after submit.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/settings", () =>
        HttpResponse.json({ ...emptySettings(), ranges: [range({ in_use: true })] }),
      ),
    );
    renderEditPage();

    expect(
      await screen.findByText("Este rango ya tiene documentos emitidos y no se puede modificar."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/^CAI$/i)).toBeDisabled();
  });
});

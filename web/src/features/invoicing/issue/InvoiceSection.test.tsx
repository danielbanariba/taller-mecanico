import { afterEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router";

import { renderWithQueryClient } from "../../../test/render";
import { server } from "../../../test/server";
import type { WorkOrderOut } from "../../workorders/api";
import { InvoiceSection } from "./InvoiceSection";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

const FISCAL_PROFILE = {
  rtn: "08019999123456",
  legal_name: "Taller Ana S. de R.L.",
  trade_name: "Taller Ana",
  address: "Col. Kennedy, Tegucigalpa",
  phone: "22223333",
  email: "taller@example.com",
  establishment_code: "001",
  emission_point_code: "001",
  updated_at: "2026-01-01T00:00:00Z",
};

const READY_SETTINGS = {
  profile: FISCAL_PROFILE,
  codes_locked: true,
  ranges: [],
  documents: [
    {
      document_type: "01",
      ready: true,
      blocked_reason: null,
      active_range_id: "range-1",
      next_number: "001-001-01-00000002",
      warnings: [],
    },
  ],
};

const ORDER: WorkOrderOut = {
  id: "order-1",
  number: 42,
  status: "completed",
  allowed_transitions: ["delivered"],
  lines_editable: true,
  active_invoice: null,
  vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
  customer: { id: "c1", full_name: "María Hernández", phone: "98765432", phone_is_mobile: true },
  complaint: null,
  odometer_km: null,
  notes: null,
  lines: [],
  total_cents: 50000,
  payments: [],
  paid_cents: 0,
  balance_cents: 50000,
  accepts_payments: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  approved_at: null,
  started_at: null,
  completed_at: "2026-01-01T00:00:00Z",
  delivered_at: null,
  cancelled_at: null,
};

/** What a real browser reports with no connection: `navigator.onLine` is false. */
function goOffline() {
  Object.defineProperty(window.navigator, "onLine", { value: false, configurable: true });
}

afterEach(() => {
  // Drops the own-property override from `goOffline`, so jsdom's own
  // `navigator.onLine` getter (always true) applies to the next test.
  Reflect.deleteProperty(window.navigator, "onLine");
});

function mockSessionAndSettings(invoices: unknown[]) {
  server.use(
    http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
    http.get("/api/invoicing/settings", () => HttpResponse.json(READY_SETTINGS)),
    http.get("/api/invoicing/invoices", () => HttpResponse.json(invoices)),
  );
}

function renderSection(order: WorkOrderOut = ORDER) {
  return renderWithQueryClient(
    <MemoryRouter>
      <InvoiceSection order={order} />
    </MemoryRouter>,
  );
}

describe("InvoiceSection", () => {
  it("lists a credited Factura together with its credit note", async () => {
    // Defect this catches: a credited Factura and its credit note
    // existing in the order's own fiscal history but never shown
    // together, leaving the owner unable to find either document again
    // from the order detail (AD-15: "Credited invoices and credit notes
    // are listed from GET /invoicing/invoices?order_id=").
    mockSessionAndSettings([
      {
        id: "invoice-1",
        number: "001-001-01-00000001",
        issued_at: "2026-01-02T10:00:00Z",
        total_cents: 50000,
        credited_at: "2026-01-03T10:00:00Z",
        credit_note: { id: "credit-note-1", number: "001-001-06-00000001", issue_date: "2026-01-03" },
      },
    ]);
    renderSection({ ...ORDER, active_invoice: null });

    const invoiceLink = await screen.findByRole("link", { name: "Ver factura 001-001-01-00000001" });
    expect(invoiceLink).toHaveAttribute("href", "/ordenes/order-1/factura/invoice-1");
    const creditNoteLink = screen.getByRole("link", { name: "Ver nota de crédito 001-001-06-00000001" });
    expect(creditNoteLink).toHaveAttribute("href", "/ordenes/order-1/nota-credito/credit-note-1");
  });

  it("offers 'Emitir factura' again once the order's only Factura has been fully credited", async () => {
    // Defect this catches: gating the issuance action on the order ever
    // having been invoiced (instead of solely on `active_invoice`),
    // which would leave a `completed` order permanently unable to
    // re-invoice after its lock was released by a credit note (AD-13).
    mockSessionAndSettings([
      {
        id: "invoice-1",
        number: "001-001-01-00000001",
        issued_at: "2026-01-02T10:00:00Z",
        total_cents: 50000,
        credited_at: "2026-01-03T10:00:00Z",
        credit_note: { id: "credit-note-1", number: "001-001-06-00000001", issue_date: "2026-01-03" },
      },
    ]);
    renderSection({ ...ORDER, active_invoice: null });

    expect(await screen.findByRole("button", { name: "Emitir factura" })).toBeInTheDocument();
  });

  it("offers 'Emitir nota de crédito' for the order's current, non-credited Factura", async () => {
    // Defect this catches: an issued Factura with a mistake having no
    // correction path from the order detail at all (AD-13 is v1's only
    // legal correction after issuance).
    mockSessionAndSettings([
      {
        id: "invoice-1",
        number: "001-001-01-00000001",
        issued_at: "2026-01-02T10:00:00Z",
        total_cents: 50000,
        credited_at: null,
        credit_note: null,
      },
    ]);
    renderSection({
      ...ORDER,
      active_invoice: { id: "invoice-1", number: "001-001-01-00000001" },
    });

    expect(await screen.findByRole("button", { name: "Emitir nota de crédito" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Emitir factura" })).not.toBeInTheDocument();
  });

  it("explains why 'Emitir factura' is disabled while offline", async () => {
    // Defect this catches: the offline explanation living only inside
    // the issue dialog, which a disabled button can never open, so an
    // offline mechanic sees a greyed-out button and no reason.
    mockSessionAndSettings([]);
    goOffline();
    renderSection();

    expect(await screen.findByRole("button", { name: "Emitir factura" })).toBeDisabled();
    expect(screen.getByText("Conéctese a internet para emitir una factura.")).toBeInTheDocument();
  });

  it("explains why 'Emitir nota de crédito' is disabled while offline", async () => {
    // Defect this catches: the same missing explanation on the credit
    // note action, or the Factura message shown for it instead.
    mockSessionAndSettings([
      {
        id: "invoice-1",
        number: "001-001-01-00000001",
        issued_at: "2026-01-02T10:00:00Z",
        total_cents: 50000,
        credited_at: null,
        credit_note: null,
      },
    ]);
    goOffline();
    renderSection({
      ...ORDER,
      active_invoice: { id: "invoice-1", number: "001-001-01-00000001" },
    });

    expect(await screen.findByRole("button", { name: "Emitir nota de crédito" })).toBeDisabled();
    expect(screen.getByText("Conéctese a internet para emitir una nota de crédito.")).toBeInTheDocument();
  });
});

import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { renderWithQueryClient } from "../../../test/render";
import { server } from "../../../test/server";
import { Invoice58Page } from "./Invoice58Page";
import type { FiscalInvoiceOut } from "../api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

const INVOICE: FiscalInvoiceOut = {
  id: "invoice-1",
  order_id: "order-1",
  order_number: 42,
  number: "001-001-01-00000001",
  issued_at: "2026-01-02T15:30:00Z",
  issue_date: "2026-01-02",
  issuer_rtn: "08019999123456",
  issuer_legal_name: "Taller Ana S. de R.L.",
  issuer_trade_name: "Taller Ana",
  issuer_address: "Col. Kennedy, Tegucigalpa",
  issuer_phone: "22223333",
  issuer_email: "taller@example.com",
  cai: "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3",
  range_first_number: "001-001-01-00000001",
  range_last_number: "001-001-01-00001000",
  issue_deadline: "2026-12-31",
  buyer_name: null,
  buyer_rtn: null,
  exempt_cents: 0,
  exonerated_cents: 0,
  discount_cents: 0,
  taxable_15_cents: 43478,
  isv_15_cents: 6522,
  total_cents: 50000,
  total_in_words: "QUINIENTOS LEMPIRAS CON 00/100",
  credited_at: null,
  credit_note: null,
  lines: [],
  created_at: "2026-01-02T15:30:00Z",
};

function renderPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/ordenes/order-1/factura/invoice-1/58mm"]}>
      <Routes>
        <Route path="/ordenes/:orderId/factura/:invoiceId/58mm" element={<Invoice58Page />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Invoice58Page", () => {
  it("prints both copies by default, ORIGINAL before COPIA, and drops the second with 'Solo original'", async () => {
    // Defect this catches: only the original copy ever being printed
    // (leaving the issuer without its own copy, Art. 10-11), or the
    // "Solo original" toggle failing to drop the second copy for a
    // reprint (`fiscal-document-print` spec's "Both Copy Destinations
    // Are Printed").
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/invoices/invoice-1", () => HttpResponse.json(INVOICE)),
    );
    const user = userEvent.setup();
    renderPage();

    const originalLegend = await screen.findAllByText("ORIGINAL: CLIENTE");
    expect(originalLegend.length).toBe(2);
    const issuerLegend = screen.getAllByText("COPIA: EMISOR");
    expect(issuerLegend.length).toBe(2);
    expect(originalLegend[0]!.compareDocumentPosition(issuerLegend[0]!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    await user.click(screen.getByRole("checkbox", { name: "Solo original" }));

    expect(screen.getAllByText("ORIGINAL: CLIENTE").length).toBe(2);
    expect(screen.queryByText("COPIA: EMISOR")).not.toBeInTheDocument();
  });
});

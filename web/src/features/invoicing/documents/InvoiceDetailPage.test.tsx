import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { sessionQueryKey } from "../../auth/hooks";
import { renderWithQueryClient } from "../../../test/render";
import { server } from "../../../test/server";
import { invoiceQueryKey } from "../hooks";
import { InvoiceDetailPage } from "./InvoiceDetailPage";
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
  issued_at: "2026-01-02T10:00:00Z",
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
  created_at: "2026-01-02T10:00:00Z",
};

function renderDetailPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/ordenes/order-1/factura/invoice-1"]}>
      <Routes>
        <Route path="/ordenes/:orderId/factura/:invoiceId" element={<InvoiceDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("InvoiceDetailPage", () => {
  it("renders the Factura's number, buyer and both print links", async () => {
    // Defect this catches: the detail screen failing to render the
    // fetched invoice at all, or omitting a link to either print layout,
    // leaving a mechanic with no way to print the document they just
    // issued.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/invoices/invoice-1", () => HttpResponse.json(INVOICE)),
    );
    renderDetailPage();

    expect(await screen.findByRole("heading", { name: "Factura 001-001-01-00000001" })).toBeInTheDocument();
    expect(screen.getByText("CONSUMIDOR FINAL")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Imprimir 58 mm" })).toHaveAttribute(
      "href",
      "/ordenes/order-1/factura/invoice-1/58mm",
    );
    expect(screen.getByRole("link", { name: "Imprimir carta" })).toHaveAttribute(
      "href",
      "/ordenes/order-1/factura/invoice-1/carta",
    );
  });

  it("keeps showing the cached Factura when the device is offline", async () => {
    // Defect this catches: a previously fetched Factura disappearing the
    // moment the device goes offline, instead of rendering from the
    // persisted cache like the order detail and both receipt layouts
    // already do (`fiscal-document-print` spec's "A previously fetched
    // document prints offline").
    server.use(
      http.get("/api/auth/me", () => HttpResponse.error()),
      http.get("/api/invoicing/invoices/invoice-1", () => HttpResponse.error()),
    );
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(sessionQueryKey, SESSION);
    queryClient.setQueryData(invoiceQueryKey("w1", "invoice-1"), INVOICE);

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/ordenes/order-1/factura/invoice-1"]}>
          <Routes>
            <Route path="/ordenes/:orderId/factura/:invoiceId" element={<InvoiceDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Factura 001-001-01-00000001" })).toBeInTheDocument();
    expect(screen.queryByText("No se encontró la factura.")).not.toBeInTheDocument();
  });

  it("offers 'Emitir nota de crédito' for a Factura that has not been credited yet", async () => {
    // Defect this catches: no way to correct a wrong Factura from its own
    // detail screen, the natural place to fix a mistake found while
    // reviewing that exact document (AD-13).
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/invoices/invoice-1", () => HttpResponse.json(INVOICE)),
    );
    renderDetailPage();

    expect(await screen.findByRole("button", { name: "Emitir nota de crédito" })).toBeInTheDocument();
  });

  it("links to the credit note instead, once the Factura has been credited", async () => {
    // Defect this catches: the detail screen still offering to issue a
    // second credit note against an already-credited Factura (A6: a
    // Factura is credited once), or never surfacing the existing
    // correction's own document at all.
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/invoices/invoice-1", () =>
        HttpResponse.json({
          ...INVOICE,
          credited_at: "2026-01-03T10:00:00Z",
          credit_note: { id: "credit-note-1", number: "001-001-06-00000001", issue_date: "2026-01-03" },
        }),
      ),
    );
    renderDetailPage();

    expect(
      await screen.findByRole("link", { name: "Ver nota de crédito 001-001-06-00000001" }),
    ).toHaveAttribute("href", "/ordenes/order-1/nota-credito/credit-note-1");
    expect(screen.queryByRole("button", { name: "Emitir nota de crédito" })).not.toBeInTheDocument();
  });
});

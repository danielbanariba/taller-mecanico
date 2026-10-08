import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { sessionQueryKey } from "../../auth/hooks";
import { renderWithQueryClient } from "../../../test/render";
import { server } from "../../../test/server";
import { creditNoteQueryKey } from "../hooks";
import { CreditNoteDetailPage } from "./CreditNoteDetailPage";
import type { FiscalCreditNoteOut } from "../api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

const CREDIT_NOTE: FiscalCreditNoteOut = {
  id: "credit-note-1",
  invoice_id: "invoice-1",
  order_id: "order-1",
  number: "001-001-06-00000001",
  issued_at: "2026-01-03T10:00:00Z",
  issue_date: "2026-01-03",
  issuer_rtn: "08019999123456",
  issuer_legal_name: "Taller Ana S. de R.L.",
  issuer_trade_name: "Taller Ana",
  issuer_address: "Col. Kennedy, Tegucigalpa",
  issuer_phone: "22223333",
  issuer_email: "taller@example.com",
  cai: "B1C2D3E4F5A6B1C2D3E4F5A6B1C2D3",
  range_first_number: "001-001-06-00000001",
  range_last_number: "001-001-06-00000100",
  issue_deadline: "2026-12-31",
  buyer_name: null,
  buyer_rtn: null,
  original_cai: "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3",
  original_number: "001-001-01-00000001",
  original_issue_date: "2026-01-02",
  reason: "Datos del comprador incorrectos",
  taxable_15_cents: 43478,
  isv_15_cents: 6522,
  total_cents: 50000,
  total_in_words: "QUINIENTOS LEMPIRAS CON 00/100",
  created_at: "2026-01-03T10:00:00Z",
};

function renderDetailPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/ordenes/order-1/nota-credito/credit-note-1"]}>
      <Routes>
        <Route path="/ordenes/:orderId/nota-credito/:creditNoteId" element={<CreditNoteDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("CreditNoteDetailPage", () => {
  it("renders the credit note's number, reason, original Factura reference and both print links", async () => {
    // Defect this catches: the detail screen failing to render the
    // fetched credit note, or omitting the reference to the Factura it
    // corrects, leaving the owner with a document nobody can trace back
    // to the original (AD-13's printed field map); or omitting a link to
    // either print layout, leaving nobody able to print the correction
    // they just issued (AD-16).
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/invoicing/credit-notes/credit-note-1", () => HttpResponse.json(CREDIT_NOTE)),
    );
    renderDetailPage();

    expect(
      await screen.findByRole("heading", { name: "Nota de crédito 001-001-06-00000001" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Datos del comprador incorrectos")).toBeInTheDocument();
    expect(screen.getByText("001-001-01-00000001")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Imprimir 58 mm" })).toHaveAttribute(
      "href",
      "/ordenes/order-1/nota-credito/credit-note-1/58mm",
    );
    expect(screen.getByRole("link", { name: "Imprimir carta" })).toHaveAttribute(
      "href",
      "/ordenes/order-1/nota-credito/credit-note-1/carta",
    );
  });

  it("keeps showing a previously fetched credit note when the device is offline", async () => {
    // Defect this catches: a previously fetched credit note disappearing
    // the moment the device goes offline, instead of rendering from the
    // persisted cache like the Factura detail screen already does
    // (`fiscal-document-print` spec's "A previously fetched document
    // prints offline").
    server.use(
      http.get("/api/auth/me", () => HttpResponse.error()),
      http.get("/api/invoicing/credit-notes/credit-note-1", () => HttpResponse.error()),
    );
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(sessionQueryKey, SESSION);
    queryClient.setQueryData(creditNoteQueryKey("w1", "credit-note-1"), CREDIT_NOTE);

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/ordenes/order-1/nota-credito/credit-note-1"]}>
          <Routes>
            <Route path="/ordenes/:orderId/nota-credito/:creditNoteId" element={<CreditNoteDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Nota de crédito 001-001-06-00000001" }),
    ).toBeInTheDocument();
  });
});

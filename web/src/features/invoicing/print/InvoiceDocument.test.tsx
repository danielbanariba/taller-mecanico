import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { InvoiceDocument } from "./InvoiceDocument";
import type { FiscalInvoiceOut } from "../api";

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
  buyer_name: "María Hernández",
  buyer_rtn: "08011990123456",
  exempt_cents: 10000,
  exonerated_cents: 20000,
  discount_cents: 5000,
  taxable_15_cents: 43478,
  isv_15_cents: 6522,
  total_cents: 50000,
  total_in_words: "QUINIENTOS LEMPIRAS CON 00/100",
  credited_at: null,
  lines: [
    {
      id: "line-1",
      position: 1,
      source_line_id: "source-1",
      kind: "labor",
      description: "Cambio de aceite",
      quantity: 1,
      unit_price_cents: 50000,
      line_total_cents: 50000,
    },
  ],
  created_at: "2026-01-02T15:30:00Z",
};

describe("InvoiceDocument", () => {
  it("renders every Printed field map Factura row", () => {
    // Defect this catches: a mandatory Art. 10-11 field missing from the
    // printed document -- the exact CT Art. 159-161 legal exposure the
    // design's own risk table names (`fiscal-document-print` spec's
    // "Every mandatory field is present on both layouts").
    render(<InvoiceDocument invoice={INVOICE} copy="original" />);

    expect(screen.getByText(/08019999123456/)).toBeInTheDocument(); // issuer RTN
    expect(screen.getByText("Taller Ana S. de R.L.")).toBeInTheDocument(); // razón social
    expect(screen.getByText("Taller Ana")).toBeInTheDocument(); // nombre comercial
    expect(screen.getByText("Col. Kennedy, Tegucigalpa")).toBeInTheDocument(); // address
    expect(screen.getByText("22223333")).toBeInTheDocument(); // phone
    expect(screen.getByText("taller@example.com")).toBeInTheDocument(); // email
    expect(screen.getByText("FACTURA")).toBeInTheDocument(); // document name
    expect(screen.getByText(/A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3/)).toBeInTheDocument(); // CAI
    expect(
      screen.getByText(/001-001-01-00000001 - 001-001-01-00001000/),
    ).toBeInTheDocument(); // rango autorizado
    expect(screen.getByText(/2026-12-31/)).toBeInTheDocument(); // fecha límite de emisión
    expect(screen.getAllByText(/001-001-01-00000001/).length).toBeGreaterThan(0); // document number
    expect(screen.getByText(/09:30/)).toBeInTheDocument(); // date and time, in Tegucigalpa local time
    expect(screen.getByText(/María Hernández/)).toBeInTheDocument(); // buyer name
    expect(screen.getByText(/08011990123456/)).toBeInTheDocument(); // buyer RTN
    expect(screen.getByText("Cambio de aceite")).toBeInTheDocument(); // line description
    expect(screen.getByRole("cell", { name: "1" })).toBeInTheDocument(); // line quantity
    expect(screen.getByText("L 500.00")).toBeInTheDocument(); // line unit value
    expect(screen.getByText(/L 100.00/)).toBeInTheDocument(); // exento
    expect(screen.getByText(/L 200.00/)).toBeInTheDocument(); // exonerado
    expect(screen.getByText(/L 50.00/)).toBeInTheDocument(); // descuento
    expect(screen.getByText(/L 434.78/)).toBeInTheDocument(); // gravado 15%
    expect(screen.getByText(/L 65.22/)).toBeInTheDocument(); // ISV 15%
    expect(screen.getByText("QUINIENTOS LEMPIRAS CON 00/100")).toBeInTheDocument(); // total in words
    expect(screen.getByText(/42/)).toBeInTheDocument(); // order reference
  });

  it("prints the issuance time in Tegucigalpa local time, never the raw UTC ISO string", () => {
    // Defect this catches: printing `invoice.issued_at` verbatim -- a raw
    // UTC ISO timestamp with microseconds -- instead of the Honduran
    // local date and time Art. 10-11 requires on every Factura.
    // Tegucigalpa is UTC-6, so 02:00 UTC on the 10th is 20:00 local on
    // the 9th; a UTC rendering would show the wrong hour and the wrong
    // day.
    render(<InvoiceDocument invoice={{ ...INVOICE, issued_at: "2026-10-10T02:00:00Z" }} copy="original" />);

    const issuedAtRow = screen.getByText(/Fecha y hora de emisión/);
    expect(issuedAtRow.textContent).toMatch(/\b0?9\b/); // the 9th, not the 10th
    expect(issuedAtRow.textContent).toMatch(/20:00|8:00/); // 20:00 local, 24h or 12h rendering
    expect(issuedAtRow.textContent).not.toMatch(/2026-10-10T02:00:00Z/);
  });

  it("renders 'CONSUMIDOR FINAL' instead of a blank when the invoice has no buyer", () => {
    // Defect this catches: a null buyer rendering as an empty field
    // instead of the legally required "CONSUMIDOR FINAL" legend
    // (`fiscal-document-print` spec references AD-11's default buyer).
    render(<InvoiceDocument invoice={{ ...INVOICE, buyer_name: null, buyer_rtn: null }} copy="original" />);

    expect(screen.getByText(/CONSUMIDOR FINAL/)).toBeInTheDocument();
  });

  it("renders zero exento, exonerado and discount amounts as 'L 0.00', never blank", () => {
    // Defect this catches: a zero amount rendered as an empty cell or
    // omitted row instead of "L 0.00" (`fiscal-document-print` spec's
    // "Zero-Value Fields Print As L 0.00, Never Blank Or Omitted").
    render(
      <InvoiceDocument
        invoice={{ ...INVOICE, exempt_cents: 0, exonerated_cents: 0, discount_cents: 0 }}
        copy="original"
      />,
    );

    expect(screen.getAllByText(/L 0.00/).length).toBe(3);
  });

  it("prints the original-to-customer legend for the 'original' copy and the copy-to-issuer legend for 'issuer'", () => {
    // Defect this catches: both printed copies carrying the same
    // destination legend, which would leave the customer or the issuer
    // with no way to tell which copy is theirs (`fiscal-document-print`
    // spec's "Both Copy Destinations Are Printed").
    const { rerender } = render(<InvoiceDocument invoice={INVOICE} copy="original" />);
    expect(screen.getAllByText("ORIGINAL: CLIENTE").length).toBe(2);
    expect(screen.queryByText("COPIA: EMISOR")).not.toBeInTheDocument();

    rerender(<InvoiceDocument invoice={INVOICE} copy="issuer" />);
    expect(screen.getAllByText("COPIA: EMISOR").length).toBe(2);
    expect(screen.queryByText("ORIGINAL: CLIENTE")).not.toBeInTheDocument();
  });
});

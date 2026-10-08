import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { CreditNoteDocument } from "./CreditNoteDocument";
import type { FiscalCreditNoteOut } from "../api";

const CREDIT_NOTE: FiscalCreditNoteOut = {
  id: "credit-note-1",
  invoice_id: "invoice-1",
  order_id: "order-1",
  number: "001-001-06-00000001",
  issued_at: "2026-01-03T15:30:00Z",
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
  buyer_name: "María Hernández",
  buyer_rtn: "08011990123456",
  original_cai: "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3",
  original_number: "001-001-01-00000001",
  original_issue_date: "2026-01-02",
  reason: "Datos del comprador incorrectos",
  taxable_15_cents: 43478,
  isv_15_cents: 6522,
  total_cents: 50000,
  total_in_words: "QUINIENTOS LEMPIRAS CON 00/100",
  created_at: "2026-01-03T15:30:00Z",
};

describe("CreditNoteDocument", () => {
  it("renders every Printed field map Nota de Crédito row", () => {
    // Defect this catches: a mandatory Art. 25-26 field missing from the
    // printed document -- the exact CT Art. 159-161 legal exposure the
    // design's own risk table names (`fiscal-document-print` spec's
    // "Every mandatory credit note field is present on both layouts").
    render(<CreditNoteDocument creditNote={CREDIT_NOTE} copy="original" />);

    expect(screen.getByText(/08019999123456/)).toBeInTheDocument(); // issuer RTN
    expect(screen.getByText("Taller Ana S. de R.L.")).toBeInTheDocument(); // razón social
    expect(screen.getByText("Taller Ana")).toBeInTheDocument(); // nombre comercial
    expect(screen.getByText("Col. Kennedy, Tegucigalpa")).toBeInTheDocument(); // address
    expect(screen.getByText("2222-3333")).toBeInTheDocument(); // phone, grouped like every other phone in the app
    expect(screen.getByText("taller@example.com")).toBeInTheDocument(); // email
    expect(screen.getByText("NOTA DE CRÉDITO")).toBeInTheDocument(); // document name
    expect(screen.getByText(/B1C2D3E4F5A6B1C2D3E4F5A6B1C2D3/)).toBeInTheDocument(); // own CAI
    expect(
      screen.getByText(/001-001-06-00000001 - 001-001-06-00000100/),
    ).toBeInTheDocument(); // own rango autorizado
    expect(screen.getByText(/2026-12-31/)).toBeInTheDocument(); // own fecha límite de emisión
    expect(screen.getAllByText(/001-001-06-00000001/).length).toBeGreaterThan(0); // document number
    expect(screen.getByText(/María Hernández/)).toBeInTheDocument(); // buyer name, copied from the Factura
    expect(screen.getByText(/08011990123456/)).toBeInTheDocument(); // buyer RTN, copied
    expect(screen.getByText(/09:30/)).toBeInTheDocument(); // date and time, in Tegucigalpa local time
    expect(screen.getByText(/L 434.78/)).toBeInTheDocument(); // gravado 15%
    expect(screen.getByText(/L 65.22/)).toBeInTheDocument(); // ISV 15%
    expect(screen.getByText(/L 500.00/)).toBeInTheDocument(); // total
    expect(screen.getByText("QUINIENTOS LEMPIRAS CON 00/100")).toBeInTheDocument(); // total in words
    expect(screen.getByText(/A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3/)).toBeInTheDocument(); // original Factura's CAI
    expect(screen.getByText(/001-001-01-00000001/)).toBeInTheDocument(); // original Factura's number
    expect(screen.getByText(/2026-01-02/)).toBeInTheDocument(); // original Factura's issue date
    expect(screen.getByText(/Datos del comprador incorrectos/)).toBeInTheDocument(); // reason
    expect(screen.getByText(/^Firma:/)).toBeInTheDocument(); // blank signature line
    expect(screen.getByText(/^Identidad:/)).toBeInTheDocument(); // blank identification line
    expect(screen.getAllByText("ORIGINAL: CLIENTE").length).toBe(2); // destination legend (both top and bottom)
  });

  it("renders 'CONSUMIDOR FINAL' instead of a blank when the original Factura had no buyer", () => {
    // Defect this catches: a null buyer copied from a consumidor final
    // Factura rendering as an empty field instead of the legally
    // required "CONSUMIDOR FINAL" legend.
    render(<CreditNoteDocument creditNote={{ ...CREDIT_NOTE, buyer_name: null, buyer_rtn: null }} copy="original" />);

    expect(screen.getByText(/CONSUMIDOR FINAL/)).toBeInTheDocument();
  });

  it("prints the original-to-customer legend for the 'original' copy and the copy-to-issuer legend for 'issuer'", () => {
    // Defect this catches: both printed copies carrying the same
    // destination legend, which would leave the customer or the issuer
    // with no way to tell which copy is theirs (`fiscal-document-print`
    // spec's "Both Copy Destinations Are Printed").
    const { rerender } = render(<CreditNoteDocument creditNote={CREDIT_NOTE} copy="original" />);
    expect(screen.getAllByText("ORIGINAL: CLIENTE").length).toBe(2);
    expect(screen.queryByText("COPIA: EMISOR")).not.toBeInTheDocument();

    rerender(<CreditNoteDocument creditNote={CREDIT_NOTE} copy="issuer" />);
    expect(screen.getAllByText("COPIA: EMISOR").length).toBe(2);
    expect(screen.queryByText("ORIGINAL: CLIENTE")).not.toBeInTheDocument();
  });
});

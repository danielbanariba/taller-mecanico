import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { formatCents } from "../../../shared/format/money";
import { vehicleLabel } from "../whatsapp";
import { ReceiptBody } from "./ReceiptBody";
import type { WorkOrderOut } from "../api";

/**
 * `formatCents` inserts a non-breaking space between the currency symbol
 * and the amount; `@testing-library/dom`'s own text normalizer collapses
 * it to a plain space before comparing, so the matcher has to go through
 * the same normalization or it never matches the rendered text.
 */
function money(cents: number): string {
  return formatCents(cents).replace(/\u00a0/g, " ");
}

const ORDER: WorkOrderOut = {
  id: "order-1",
  number: 42,
  status: "completed",
  allowed_transitions: ["delivered"],
  lines_editable: false,
  active_invoice: null,
  vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
  customer: { id: "c1", full_name: "María Hernández", phone: "98765432", phone_is_mobile: true },
  complaint: null,
  odometer_km: null,
  notes: null,
  lines: [
    {
      id: "line-1",
      kind: "labor",
      item_id: null,
      description: "Cambio de aceite",
      quantity: 1,
      unit_price_cents: 30000,
      line_total_cents: 30000,
      stock_posted_quantity: 0,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
    {
      id: "line-2",
      kind: "inventory_part",
      item_id: "item-1",
      description: "Filtro de aceite",
      quantity: 2,
      unit_price_cents: 10000,
      line_total_cents: 20000,
      stock_posted_quantity: 2,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  ],
  total_cents: 50000,
  payments: [],
  paid_cents: 50000,
  balance_cents: 0,
  accepts_payments: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  approved_at: null,
  started_at: null,
  completed_at: "2026-01-02T00:00:00Z",
  delivered_at: null,
  cancelled_at: null,
};

describe("ReceiptBody", () => {
  it("shows the mandatory non-fiscal label, so the receipt is never mistaken for a tax invoice", () => {
    render(<ReceiptBody order={ORDER} />);
    // Repeated top and bottom per `design.md`'s AD-19, so it stays visible
    // however the printed content paginates.
    expect(screen.getAllByText("DOCUMENTO NO FISCAL — No válido como factura")).toHaveLength(2);
  });

  it("shows a fully paid order's total, paid total and a zero balance due", () => {
    render(<ReceiptBody order={ORDER} />);
    expect(screen.getAllByText(money(50000))).toHaveLength(2); // total and paid both 500.00
    expect(screen.getByText(money(0))).toBeInTheDocument();
  });

  it("shows a partially paid order's balance due, not a zero or the full total", () => {
    // 100.00/400.00 (not 300.00 or 200.00, so this never collides with
    // either line's own subtotal below).
    const partiallyPaid: WorkOrderOut = { ...ORDER, paid_cents: 10000, balance_cents: 40000 };
    render(<ReceiptBody order={partiallyPaid} />);
    expect(screen.getByText(money(40000))).toBeInTheDocument();
  });

  it("renders the order number, vehicle, customer and each line's own subtotal", () => {
    render(<ReceiptBody order={ORDER} />);
    expect(screen.getByText("Orden #42")).toBeInTheDocument();
    expect(screen.getByText(vehicleLabel(ORDER))).toBeInTheDocument();
    expect(screen.getByText("María Hernández")).toBeInTheDocument();
    expect(screen.getByText(/Cambio de aceite/)).toBeInTheDocument();
    // line-2's own subtotal (2 x 100.00), not its unit price alone.
    expect(screen.getByText(money(20000))).toBeInTheDocument();
  });
});

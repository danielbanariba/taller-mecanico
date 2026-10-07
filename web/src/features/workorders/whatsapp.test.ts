import { afterEach, describe, expect, it } from "vitest";

import { formatCents } from "../../shared/format/money";
import { buildOrderSummary, buildWhatsAppUrl, supportsFileShare } from "./whatsapp";
import type { WorkOrderLineOut, WorkOrderOut } from "./api";

function line(overrides: Partial<WorkOrderLineOut> = {}): WorkOrderLineOut {
  return {
    id: "line-1",
    kind: "labor",
    item_id: null,
    description: "Cambio de aceite",
    quantity: 1,
    unit_price_cents: 50000,
    line_total_cents: 50000,
    stock_posted_quantity: 0,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function order(overrides: Partial<WorkOrderOut> = {}): WorkOrderOut {
  return {
    id: "order-1",
    number: 42,
    status: "quote",
    allowed_transitions: ["approved", "cancelled"],
    lines_editable: true,
    vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
    customer: { id: "c1", full_name: "María Hernández", phone: "98765432", phone_is_mobile: true },
    complaint: null,
    odometer_km: null,
    notes: null,
    lines: [line()],
    total_cents: 50000,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    approved_at: null,
    started_at: null,
    completed_at: null,
    delivered_at: null,
    cancelled_at: null,
    ...overrides,
  };
}

describe("buildWhatsAppUrl", () => {
  it("prefixes Honduras' country code and URL-encodes the message", () => {
    // Defect this catches: a missing `504` country code (the link opens
    // the wrong chat, or none), or an unencoded `&`/`#` that WhatsApp's
    // own query-string parsing would truncate the message at.
    expect(buildWhatsAppUrl("98765432", "a & b #2")).toBe("https://wa.me/50498765432?text=a%20%26%20b%20%232");
  });
});

describe("buildOrderSummary", () => {
  it("includes the order number, vehicle, every line and the formatted total", () => {
    // Defect this catches: the summary omitting a line kind, or leaking
    // raw integer cents (e.g. "50000") to the customer instead of the
    // formatted amount (the `whatsapp-sharing` spec's own wording).
    const summary = buildOrderSummary(
      order({
        lines: [line({ description: "Cambio de aceite" }), line({ id: "line-2", description: "Filtro de aceite" })],
      }),
      "Taller Ana",
    );

    expect(summary).toContain("42");
    expect(summary).toContain("Toyota Corolla");
    expect(summary).toContain("Cambio de aceite");
    expect(summary).toContain("Filtro de aceite");
    expect(summary).toContain(formatCents(50000));
    expect(summary).not.toContain("50000");
  });
});

describe("supportsFileShare", () => {
  afterEach(() => {
    Reflect.deleteProperty(navigator, "canShare");
  });

  it("is false when the browser has no canShare", () => {
    // Defect this catches: offering the photo-attach step on a browser
    // that cannot actually invoke the Web Share API with files, which
    // the `whatsapp-sharing` spec forbids ("Fallback on a non-supporting
    // browser").
    expect(supportsFileShare()).toBe(false);
  });

  it("is false when canShare exists but reports no file support", () => {
    Object.defineProperty(navigator, "canShare", { value: () => false, configurable: true });
    expect(supportsFileShare()).toBe(false);
  });

  it("is true when canShare reports file support", () => {
    // Defect this catches: never offering the photo-attach step on a
    // browser that genuinely supports it.
    Object.defineProperty(navigator, "canShare", { value: () => true, configurable: true });
    expect(supportsFileShare()).toBe(true);
  });
});

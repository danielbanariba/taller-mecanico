import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ShareWhatsAppButton } from "./ShareWhatsAppButton";
import { buildOrderSummary, buildWhatsAppUrl } from "./whatsapp";
import type { WorkOrderOut } from "./api";

function order(customerOverrides: Partial<WorkOrderOut["customer"]> = {}): WorkOrderOut {
  return {
    id: "order-1",
    number: 42,
    status: "quote",
    allowed_transitions: ["approved", "cancelled"],
    lines_editable: true,
    vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
    customer: { id: "c1", full_name: "María Hernández", phone: "98765432", phone_is_mobile: true, ...customerOverrides },
    complaint: null,
    odometer_km: null,
    notes: null,
    lines: [],
    total_cents: 0,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    approved_at: null,
    started_at: null,
    completed_at: null,
    delivered_at: null,
    cancelled_at: null,
  };
}

describe("ShareWhatsAppButton", () => {
  it("renders nothing for a landline-only customer", () => {
    // Defect this catches: offering WhatsApp sharing to a customer the
    // `whatsapp-sharing` spec says must never see it.
    render(<ShareWhatsAppButton order={order({ phone_is_mobile: false })} workshopName="Taller Ana" />);
    expect(screen.queryByText("Compartir por WhatsApp")).not.toBeInTheDocument();
  });

  it("renders nothing for a phoneless customer", () => {
    // Defect this catches: a null `phone_is_mobile` (no phone recorded)
    // being treated as truthy enough to still show the share action.
    render(<ShareWhatsAppButton order={order({ phone_is_mobile: null, phone: null })} workshopName="Taller Ana" />);
    expect(screen.queryByText("Compartir por WhatsApp")).not.toBeInTheDocument();
  });

  it("is a plain link to wa.me when the browser cannot share files", () => {
    // Defect this catches: the photo-attach step being offered on a
    // browser that cannot actually invoke it, leaving the mechanic with
    // a dialog that can never send ("Fallback on a non-supporting
    // browser" in the `whatsapp-sharing` spec). jsdom's `navigator` has
    // no `canShare`, so no stubbing is needed to exercise this branch.
    const data = order();
    render(<ShareWhatsAppButton order={data} workshopName="Taller Ana" />);

    const link = screen.getByRole("link", { name: "Compartir por WhatsApp" });
    expect(link).toHaveAttribute(
      "href",
      buildWhatsAppUrl(data.customer.phone as string, buildOrderSummary(data, "Taller Ana")),
    );
  });

  describe("when the browser supports file sharing", () => {
    afterEach(() => {
      Reflect.deleteProperty(navigator, "canShare");
      Reflect.deleteProperty(navigator, "share");
    });

    it("shares the selected photos and the summary through the Web Share API", async () => {
      // Defect this catches: the photo-attach step never actually
      // reaching `navigator.share`, or dropping the files/text payload
      // ("Photo sharing on a supporting browser" in the `whatsapp-sharing`
      // spec).
      Object.defineProperty(navigator, "canShare", { value: () => true, configurable: true });
      const shareSpy = vi.fn().mockResolvedValue(undefined);
      Object.defineProperty(navigator, "share", { value: shareSpy, configurable: true });
      const data = order();
      const user = userEvent.setup();
      render(<ShareWhatsAppButton order={data} workshopName="Taller Ana" />);

      await user.click(screen.getByRole("button", { name: "Compartir por WhatsApp" }));
      const file = new File(["foto"], "foto.jpg", { type: "image/jpeg" });
      const input = await screen.findByLabelText("Fotos (opcional)");
      await user.upload(input, file);
      await user.click(screen.getByRole("button", { name: "Enviar" }));

      await waitFor(() =>
        expect(shareSpy).toHaveBeenCalledWith({ files: [file], text: buildOrderSummary(data, "Taller Ana") }),
      );
    });
  });
});

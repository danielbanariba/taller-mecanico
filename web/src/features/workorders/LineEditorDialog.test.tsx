import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { LineEditorDialog, type LineEditorValues } from "./LineEditorDialog";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

function itemResponse() {
  return {
    id: "item-1",
    name: "Filtro de aceite",
    category: "Filtros",
    unit: "unidad",
    min_stock: 2,
    sale_price_cents: 5000,
    notes: null,
    stock: 10,
    needs_review: false,
    is_low: false,
    archived_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

function renderDialog(overrides: Partial<Parameters<typeof LineEditorDialog>[0]> = {}) {
  const onSubmit = overrides.onSubmit ?? vi.fn();
  const onClose = overrides.onClose ?? vi.fn();
  renderWithQueryClient(
    <LineEditorDialog
      open
      mode="create"
      pending={false}
      offline={false}
      onClose={onClose}
      onSubmit={onSubmit}
      {...overrides}
    />,
  );
  return { onSubmit, onClose };
}

describe("LineEditorDialog", () => {
  it("rejects a part line with no item selected", async () => {
    // Defect this catches: submitting an inventory-part line with no
    // `item_id` would hit the API's 422 `item_id is required for
    // inventory_part lines only` validator with no client-side
    // explanation, or worse, silently submit `itemId: undefined` as if it
    // were a valid part line.
    server.use(http.get("/api/auth/me", () => HttpResponse.json(SESSION)));
    const user = userEvent.setup();
    const { onSubmit } = renderDialog();

    // Description, quantity and price are all otherwise valid, so the only
    // thing that can still block this submit is the missing item -- a test
    // that left description blank too would pass even if the item-required
    // check were deleted entirely, since the blank description would block
    // the submit on its own.
    await user.click(screen.getByRole("button", { name: /repuesto de inventario/i }));
    await user.type(screen.getByLabelText(/descripción/i), "Filtro de aceite");
    await user.type(screen.getByLabelText(/precio unitario/i), "150");
    await user.click(screen.getByRole("button", { name: /guardar línea/i }));

    expect(screen.getByText("Seleccione un repuesto.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("previews a part line's subtotal from local input alone, never posting a stock movement", async () => {
    // Defect this catches: wiring the item picker or the quantity preview
    // through inventory's optimistic stock mutation (`useRecordMovement`)
    // would move stock the moment a part is picked, before the line is
    // even saved -- the `work-orders` spec is explicit that adding a line
    // posts no movement until the order actually consumes it.
    let movementWasCalled = false;
    server.use(
      http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
      http.get("/api/inventory/items", () => HttpResponse.json([itemResponse()])),
      http.put("/api/inventory/movements/:id", () => {
        movementWasCalled = true;
        return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
      }),
    );
    const user = userEvent.setup();
    const { onSubmit } = renderDialog();

    await user.click(screen.getByRole("button", { name: /repuesto de inventario/i }));
    await user.click(screen.getByRole("button", { name: /seleccionar repuesto/i }));
    await user.click(await screen.findByText("Filtro de aceite"));

    const quantityField = screen.getByLabelText(/cantidad/i);
    await user.clear(quantityField);
    await user.type(quantityField, "3");

    expect(screen.getByText("L 150.00")).toBeInTheDocument();
    expect(movementWasCalled).toBe(false);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits a labor line's description, quantity and price once valid", async () => {
    // Defect this catches: a valid labor line (which needs no item at
    // all) being blocked by the same item-required guard that only
    // applies to inventory-part lines.
    server.use(http.get("/api/auth/me", () => HttpResponse.json(SESSION)));
    const user = userEvent.setup();
    const { onSubmit } = renderDialog();

    await user.type(screen.getByLabelText(/descripción/i), "Cambio de aceite");
    await user.clear(screen.getByLabelText(/cantidad/i));
    await user.type(screen.getByLabelText(/cantidad/i), "1");
    await user.type(screen.getByLabelText(/precio unitario/i), "500");
    await user.click(screen.getByRole("button", { name: /guardar línea/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      kind: "labor",
      itemId: undefined,
      description: "Cambio de aceite",
      quantity: 1,
      unitPriceCents: 50000,
    } satisfies LineEditorValues);
  });
});

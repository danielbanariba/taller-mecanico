import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ItemForm } from "./ItemForm";

const BASE_PROPS = {
  categorySuggestions: [],
  pending: false,
  submitLabel: "Guardar repuesto",
  submitPendingLabel: "Guardando...",
};

describe("ItemForm client-side upper bounds", () => {
  it("rejects a name longer than 120 characters and does not call onSubmit", async () => {
    // Defect this catches: ItemForm only checked for an empty name, so an
    // arbitrarily long name (no practical display or storage limit) could
    // reach the API instead of being caught client-side.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ItemForm mode="create" {...BASE_PROPS} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/^nombre$/i), "a".repeat(121));
    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(await screen.findByText(/no puede tener más de 120 caracteres/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("accepts a name that is exactly 120 characters", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ItemForm mode="create" {...BASE_PROPS} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/^nombre$/i), "a".repeat(120));
    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("rejects an initial stock above 1,000,000 and does not call onSubmit", async () => {
    // Defect this catches: no upper bound on initial_stock let a value far
    // beyond anything a shop could hold reach the API unvalidated.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ItemForm mode="create" {...BASE_PROPS} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/^nombre$/i), "Filtro de aceite");
    const initialStockField = screen.getByLabelText(/cantidad actual/i);
    await user.clear(initialStockField);
    await user.type(initialStockField, "1000001");
    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(await screen.findByText(/entre 0 y 1,000,000/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("rejects a minimum stock above 1,000,000 and does not call onSubmit", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ItemForm mode="create" {...BASE_PROPS} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/^nombre$/i), "Filtro de aceite");
    const minStockField = screen.getByLabelText(/mínimo para avisar/i);
    await user.clear(minStockField);
    await user.type(minStockField, "1000001");
    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(await screen.findByText(/entre 0 y 1,000,000/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("rejects a price above L 10,000,000.00 and does not call onSubmit", async () => {
    // Defect this catches: ItemForm only checked that the price was
    // well-formed, not that it stayed within the API's bound (1,000,000,000
    // cents), so a price like 99,999,999.99 could reach the API unvalidated.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ItemForm mode="create" {...BASE_PROPS} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/^nombre$/i), "Filtro de aceite");
    await user.type(screen.getByLabelText(/precio de venta/i), "10,000,000.01");
    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(await screen.findByText(/no puede ser mayor a L 10,000,000.00/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});

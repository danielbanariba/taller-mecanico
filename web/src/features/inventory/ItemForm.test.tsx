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

describe("ItemForm category and unit suggestion chips", () => {
  it("fills the category field and submits it when a suggestion chip is tapped", async () => {
    // Defect this catches: a chip that renders but isn't wired to update the
    // category field, so tapping a visible suggestion does nothing and the
    // mechanic still has to retype a value already on screen.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(
      <ItemForm mode="create" {...BASE_PROPS} categorySuggestions={["Frenos", "Motor"]} onSubmit={onSubmit} />,
    );

    await user.type(screen.getByLabelText(/^nombre$/i), "Pastillas delanteras");
    await user.click(screen.getByRole("button", { name: "Frenos" }));
    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toMatchObject({ category: "Frenos" });
  });

  it("still submits a hand-typed category that is not among the suggestions", async () => {
    // Defect this catches: turning the category field into a chip-only
    // picker (e.g. making the input read-only) would make it impossible to
    // save a category that has never been used before.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(
      <ItemForm mode="create" {...BASE_PROPS} categorySuggestions={["Frenos", "Motor"]} onSubmit={onSubmit} />,
    );

    await user.type(screen.getByLabelText(/^nombre$/i), "Pastillas delanteras");
    await user.type(screen.getByLabelText(/^categoría$/i), "Suspensión");
    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toMatchObject({ category: "Suspensión" });
  });

  it("fills the unit field and submits it when a suggestion chip is tapped", async () => {
    // Defect this catches: the same chip-wiring mistake on the unit field,
    // which already has a default value, so a chip tap that silently fails
    // to update it would be easy to miss visually.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ItemForm mode="create" {...BASE_PROPS} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/^nombre$/i), "Aceite de motor");
    await user.click(screen.getByRole("button", { name: "galón" }));
    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toMatchObject({ unit: "galón" });
  });

  it("still submits a hand-typed unit that is not among the suggestions", async () => {
    // Defect this catches: a chip-only unit picker would make an unusual,
    // never-suggested unit (e.g. "bolsa") impossible to save.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ItemForm mode="create" {...BASE_PROPS} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/^nombre$/i), "Empaques");
    const unitField = screen.getByLabelText(/^unidad$/i);
    await user.clear(unitField);
    await user.type(unitField, "bolsa");
    await user.click(screen.getByRole("button", { name: /guardar repuesto/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toMatchObject({ unit: "bolsa" });
  });
});

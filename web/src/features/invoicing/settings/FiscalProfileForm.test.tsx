import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FiscalProfileForm } from "./FiscalProfileForm";

describe("FiscalProfileForm", () => {
  it("submits every required field, trimmed", async () => {
    // Defect this catches: a field rendered but never read into the
    // object `onSubmit` receives, which would reach `PUT
    // /invoicing/profile` incomplete and fail its own "every field
    // mandatory" validation (AD-3) for no reason visible to the user.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<FiscalProfileForm onSubmit={onSubmit} pending={false} />);

    await user.type(screen.getByLabelText(/razón social/i), "  Taller Ana S. de R.L.  ");
    await user.type(screen.getByLabelText(/nombre comercial/i), "Taller Ana");
    await user.type(screen.getByLabelText(/^RTN$/i), "08011990123456");
    await user.type(screen.getByLabelText(/dirección/i), "Col. Kennedy");
    await user.type(screen.getByLabelText(/teléfono/i), "22000000");
    await user.type(screen.getByLabelText(/correo electrónico/i), "demo@example.invalid");
    await user.type(screen.getByLabelText(/código de establecimiento/i), "001");
    await user.type(screen.getByLabelText(/código de punto de emisión/i), "001");
    await user.click(screen.getByRole("button", { name: /guardar datos fiscales/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      legalName: "Taller Ana S. de R.L.",
      tradeName: "Taller Ana",
      rtn: "08011990123456",
      address: "Col. Kennedy",
      phone: "22000000",
      email: "demo@example.invalid",
      establishmentCode: "001",
      emissionPointCode: "001",
    });
  });

  it("blocks submission and shows a required message while any field is still empty", async () => {
    // Defect this catches: a half-filled profile reaching the server,
    // which would either be silently rejected or (worse) accepted with
    // a required field missing.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<FiscalProfileForm onSubmit={onSubmit} pending={false} />);

    await user.type(screen.getByLabelText(/razón social/i), "Taller Ana S. de R.L.");
    await user.click(screen.getByRole("button", { name: /guardar datos fiscales/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText("El nombre comercial es obligatorio.")).toBeInTheDocument();
  });

  it("disables submission and explains why when offline", () => {
    // Defect this catches: a profile write attempted (or silently
    // allowed) offline, when the API it needs is unreachable anyway.
    render(<FiscalProfileForm onSubmit={vi.fn()} pending={false} offline />);

    expect(screen.getByText("Conéctese a internet para guardar los datos fiscales.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /guardar datos fiscales/i })).toBeDisabled();
  });
});

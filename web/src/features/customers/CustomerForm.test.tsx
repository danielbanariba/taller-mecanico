import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CustomerForm } from "./CustomerForm";

describe("CustomerForm", () => {
  it("submits the billing name and RTN entered by the user, trimmed, alongside the other fields", async () => {
    // Defect this catches: the billing name/RTN inputs rendered in the JSX
    // but never actually read into the object `onSubmit` receives (e.g. a
    // field added to the form but forgotten in the submit handler), which
    // would silently drop fiscal data the `sar-invoicing` customers delta
    // requires before it ever reaches the API.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(
      <CustomerForm
        mode="create"
        onSubmit={onSubmit}
        pending={false}
        submitLabel="Guardar cliente"
        submitPendingLabel="Guardando..."
      />,
    );

    await user.type(screen.getByLabelText(/nombre completo/i), "María Hernández");
    await user.type(screen.getByLabelText(/nombre de facturación/i), "  Taller María S. de R.L.  ");
    await user.type(screen.getByLabelText(/^RTN$/i), "  0801-1990-123456  ");
    await user.click(screen.getByRole("button", { name: /guardar cliente/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      fullName: "María Hernández",
      phone: "",
      notes: "",
      billingName: "Taller María S. de R.L.",
      rtn: "0801-1990-123456",
    });
  });

  it("renders no billing name or RTN pre-filled when the customer has neither", () => {
    // Defect this catches: a literal "null"/"undefined" string rendered
    // into the input value instead of an empty field, when editing a
    // customer that never set these optional fields.
    render(
      <CustomerForm
        mode="edit"
        initialValues={{ fullName: "María Hernández", phone: "", notes: "", billingName: "", rtn: "" }}
        onSubmit={vi.fn()}
        pending={false}
        submitLabel="Guardar cambios"
        submitPendingLabel="Guardando..."
      />,
    );

    expect(screen.getByLabelText(/nombre de facturación/i)).toHaveValue("");
    expect(screen.getByLabelText(/^RTN$/i)).toHaveValue("");
  });
});

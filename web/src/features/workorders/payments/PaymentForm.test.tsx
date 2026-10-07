import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PaymentForm, type PaymentFormValues } from "./PaymentForm";

function renderForm(overrides: Partial<Parameters<typeof PaymentForm>[0]> = {}) {
  const onSubmit = overrides.onSubmit ?? vi.fn();
  render(<PaymentForm pending={false} offline={false} onSubmit={onSubmit} {...overrides} />);
  return { onSubmit };
}

describe("PaymentForm", () => {
  it("parses a thousands-grouped amount into integer cents, matching what formatCents displays", async () => {
    // Defect this catches: a thousands separator (as shown by `formatCents`,
    // e.g. "L 1,500.50") mis-parsed into the wrong cent amount when the
    // mechanic retypes a price exactly as the app showed it.
    const user = userEvent.setup();
    const { onSubmit } = renderForm();

    await user.type(screen.getByLabelText("Monto del pago"), "1,500.50");
    await user.click(screen.getByRole("button", { name: "Registrar pago" }));

    expect(onSubmit).toHaveBeenCalledWith({
      amountCents: 150050,
      method: "cash",
      note: undefined,
    } satisfies PaymentFormValues);
  });

  it("rejects a zero or negative amount, never submitting it", async () => {
    // Defect this catches: a payment of 0 (or a negative amount, if
    // `parseLempirasToCents` ever accepted a leading `-`) reaching the API,
    // which the `payments` spec's amount bound would otherwise only catch
    // server-side with no client-facing explanation.
    const user = userEvent.setup();
    const { onSubmit } = renderForm();

    await user.type(screen.getByLabelText("Monto del pago"), "0");
    await user.click(screen.getByRole("button", { name: "Registrar pago" }));

    expect(screen.getByText("El monto no es válido.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});

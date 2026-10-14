import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { formatCents } from "../../../shared/format/money";
import { PaymentForm, type PaymentFormValues } from "./PaymentForm";

/** Builds the expected text for an amount with a plain space in place of
 * `formatCents`'s non-breaking one, matching the DOM text the default
 * testing-library normalizer produces (see `receipt/ReceiptBody.test.tsx`'s
 * own `money()` helper for the same reason). */
function money(cents: number): string {
  return formatCents(cents).replace(/\u00a0/g, " ");
}

function renderForm(overrides: Partial<Parameters<typeof PaymentForm>[0]> = {}) {
  const onSubmit = overrides.onSubmit ?? vi.fn();
  render(<PaymentForm pending={false} offline={false} balanceCents={1_000_000} onSubmit={onSubmit} {...overrides} />);
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

  it("shows the change and caps a cash payment at the balance when the amount received is larger", async () => {
    // Defect this catches: a cash payment larger than the balance either
    // gets rejected the way every other method does, or is submitted in
    // full instead of only the balance, silently recording more than the
    // order actually owes and never telling the mechanic the change due.
    const user = userEvent.setup();
    const { onSubmit } = renderForm({ balanceCents: 30000 });

    await user.type(screen.getByLabelText("Monto del pago"), "500");

    expect(screen.getByText(`Vuelto: ${money(20000)}`)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Registrar pago" }));

    expect(onSubmit).toHaveBeenCalledWith({
      amountCents: 30000,
      method: "cash",
      note: undefined,
    } satisfies PaymentFormValues);
  });

  it("blocks a non-cash amount over the balance client-side, with the same message the server would use", async () => {
    // Defect this catches: a transfer/card/other payment larger than the
    // balance reaching `onSubmit` (and so the API) instead of being
    // blocked the moment it is typed, now that cash no longer blocks an
    // over-balance amount the same way.
    const user = userEvent.setup();
    const { onSubmit } = renderForm({ balanceCents: 30000 });

    await user.click(screen.getByRole("button", { name: "Tarjeta" }));
    await user.type(screen.getByLabelText("Monto del pago"), "500");
    await user.click(screen.getByRole("button", { name: "Registrar pago" }));

    expect(screen.getByText("El monto supera el saldo pendiente.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("hides the stale server error banner while a current field error is showing", async () => {
    // Defect this catches: emptying the amount field after a rejected
    // payment and resubmitting shows both the leftover server banner
    // (the parent's last mutation error) and the field's own validation
    // message at once, instead of only the one that is actually current.
    const user = userEvent.setup();
    renderForm({ errorMessage: "El monto supera el saldo pendiente." });

    await user.click(screen.getByRole("button", { name: "Registrar pago" }));

    expect(screen.getByText("El monto no es válido.")).toBeInTheDocument();
    expect(screen.queryByText("El monto supera el saldo pendiente.")).not.toBeInTheDocument();
  });
});

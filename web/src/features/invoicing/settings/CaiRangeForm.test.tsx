import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CaiRangeForm } from "./CaiRangeForm";

describe("CaiRangeForm", () => {
  it("offers both Factura (01) and Nota de crédito (06) as document types, selectable for a new range", () => {
    // Defect this catches: the form never offering `06` at all, leaving
    // no way for a workshop to register a credit-note range from the
    // app (Phase B's `cai-ranges` spec accepts `06` from `create_range`
    // onward; the range form must offer every document type the API
    // now accepts).
    render(<CaiRangeForm onSubmit={vi.fn()} pending={false} />);

    const select = screen.getByLabelText(/tipo de documento/i) as HTMLSelectElement;
    const options = within(select).getAllByRole("option");
    expect(options).toHaveLength(2);
    expect(options[0]).toHaveTextContent("Factura");
    expect(options[1]).toHaveTextContent("Nota de crédito");
    expect(select).toHaveValue("01");
    expect(select).not.toBeDisabled();
  });

  it("submits the selected document type when 'Nota de crédito' is chosen", async () => {
    // Defect this catches: the select rendering `06` as an option but
    // the submitted payload staying hardcoded to `01`, which would
    // register a Factura range while the user believed they registered
    // a credit-note range.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CaiRangeForm onSubmit={onSubmit} pending={false} />);

    await user.selectOptions(screen.getByLabelText(/tipo de documento/i), "06");
    await user.type(screen.getByLabelText(/^CAI$/i), "ABCD-1234-EFGH-5678");
    await user.type(screen.getByLabelText(/número inicial/i), "1");
    await user.type(screen.getByLabelText(/número final/i), "100");
    await user.type(screen.getByLabelText(/fecha límite/i), "2027-01-01");
    await user.click(screen.getByRole("button", { name: /guardar rango/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ documentType: "06", rangeStart: 1, rangeEnd: 100 }),
    );
  });

  it("submits the CAI and the numeric bounds parsed from the text inputs, trimmed", async () => {
    // Defect this catches: the bounds sent as strings (or with stray
    // whitespace) instead of the integers `POST /invoicing/cai-ranges`
    // expects, which would fail validation or round-trip incorrectly.
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CaiRangeForm onSubmit={onSubmit} pending={false} />);

    await user.type(screen.getByLabelText(/^CAI$/i), "  ABCD-1234-EFGH-5678  ");
    await user.type(screen.getByLabelText(/número inicial/i), "1");
    await user.type(screen.getByLabelText(/número final/i), "500");
    await user.type(screen.getByLabelText(/fecha límite/i), "2027-01-01");
    await user.click(screen.getByRole("button", { name: /guardar rango/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      documentType: "01",
      cai: "ABCD-1234-EFGH-5678",
      rangeStart: 1,
      rangeEnd: 500,
      issueDeadline: "2027-01-01",
    });
  });

  it("disables every field with an explanation once the range already has documents issued", () => {
    // Defect this catches: editing an in-use range's bounds (AD-4's
    // immutability rule) submitted anyway, only to be rejected by the
    // server with 409 `cai_range_immutable` -- the UI must disable it
    // up front with an explanation instead.
    render(
      <CaiRangeForm
        initialValues={{ cai: "ABCDEFGHIJ1234567890", rangeStart: "1", rangeEnd: "500", issueDeadline: "2027-01-01" }}
        inUse
        onSubmit={vi.fn()}
        pending={false}
      />,
    );

    expect(screen.getByText("Este rango ya tiene documentos emitidos y no se puede modificar.")).toBeInTheDocument();
    expect(screen.getByLabelText(/tipo de documento/i)).toBeDisabled();
    expect(screen.getByLabelText(/^CAI$/i)).toBeDisabled();
    expect(screen.getByLabelText(/número inicial/i)).toBeDisabled();
    expect(screen.getByLabelText(/número final/i)).toBeDisabled();
    expect(screen.getByLabelText(/fecha límite/i)).toBeDisabled();
    expect(screen.queryByRole("button", { name: /guardar rango/i })).not.toBeInTheDocument();
  });

  it("disables submission and explains why when offline", async () => {
    // Defect this catches: a range write attempted (or silently allowed)
    // offline, when the API it needs is unreachable anyway.
    const onSubmit = vi.fn();
    render(<CaiRangeForm onSubmit={onSubmit} pending={false} offline />);

    expect(
      screen.getByText("Conéctese a internet para registrar o editar un rango de CAI."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /guardar rango/i })).toBeDisabled();
  });
});

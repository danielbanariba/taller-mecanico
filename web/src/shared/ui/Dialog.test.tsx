import { useState } from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Dialog } from "./Dialog";

/** A page with a button that opens the dialog, and one more control behind it. */
function DialogHarness() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>
        Abrir
      </button>
      <button type="button">Detrás del diálogo</button>
      <Dialog open={open} title="Contar repuesto" onClose={() => setOpen(false)}>
        <input aria-label="Cantidad contada" />
        <button type="button" onClick={() => setOpen(false)}>
          Cancelar
        </button>
        <button type="button">Guardar conteo</button>
      </Dialog>
    </>
  );
}

async function openDialog() {
  const user = userEvent.setup();
  render(<DialogHarness />);
  await user.click(screen.getByRole("button", { name: "Abrir" }));
  return user;
}

describe("Dialog", () => {
  it("moves focus into the dialog on open and back to the button that opened it on close", async () => {
    // Defect this catches: focus left on the page behind the modal (a
    // keyboard or screen-reader user keeps operating what the dialog
    // covers), and lost to <body> after closing it.
    const user = await openDialog();

    expect(screen.getByLabelText("Cantidad contada")).toHaveFocus();

    await user.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Abrir" })).toHaveFocus();
  });

  it("closes on Escape and returns focus to the button that opened it", async () => {
    // Defect this catches: a modal with no keyboard way out.
    const user = await openDialog();

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Abrir" })).toHaveFocus();
  });

  it("keeps Tab and Shift+Tab inside the dialog while it is open", async () => {
    // Defect this catches: tabbing past the last control lands on the page
    // the modal covers ("Detrás del diálogo"), which it claims is inert.
    const user = await openDialog();
    const first = screen.getByLabelText("Cantidad contada");
    const last = screen.getByRole("button", { name: "Guardar conteo" });

    await user.tab();
    await user.tab();
    expect(last).toHaveFocus();
    await user.tab();
    expect(first).toHaveFocus();
    await user.tab({ shift: true });
    expect(last).toHaveFocus();
    expect(screen.getByRole("button", { name: "Detrás del diálogo" })).not.toHaveFocus();
  });
});

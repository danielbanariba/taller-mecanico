import { afterEach, describe, expect, it } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router";

import { renderWithQueryClient } from "../../../test/render";
import { server } from "../../../test/server";
import { workOrderQueryKey } from "../../workorders/hooks";
import { invoiceQueryKey, invoicingSettingsQueryKey, orderInvoicesQueryKey } from "../hooks";
import { CreditNoteDialog } from "./CreditNoteDialog";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

const CREDIT_NOTE = {
  id: "credit-note-1",
  invoice_id: "invoice-1",
  order_id: "order-1",
  number: "001-001-06-00000001",
  issued_at: "2026-01-03T10:00:00Z",
  issue_date: "2026-01-03",
  issuer_rtn: "08019999123456",
  issuer_legal_name: "Taller Ana S. de R.L.",
  issuer_trade_name: "Taller Ana",
  issuer_address: "Col. Kennedy, Tegucigalpa",
  issuer_phone: "22223333",
  issuer_email: "taller@example.com",
  cai: "B1C2D3E4F5A6B1C2D3E4F5A6B1C2D3",
  range_first_number: "001-001-06-00000001",
  range_last_number: "001-001-06-00000100",
  issue_deadline: "2026-12-31",
  buyer_name: null,
  buyer_rtn: null,
  original_cai: "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3",
  original_number: "001-001-01-00000001",
  original_issue_date: "2026-01-02",
  reason: "Datos del comprador incorrectos",
  taxable_15_cents: 43478,
  isv_15_cents: 6522,
  total_cents: 50000,
  total_in_words: "QUINIENTOS LEMPIRAS CON 00/100",
  created_at: "2026-01-03T10:00:00Z",
};

function mockSession() {
  server.use(http.get("/api/auth/me", () => HttpResponse.json(SESSION)));
}

function renderDialog() {
  return renderWithQueryClient(
    <MemoryRouter>
      <CreditNoteDialog open orderId="order-1" invoiceId="invoice-1" onClose={() => {}} />
    </MemoryRouter>,
  );
}

/** What a real browser does when the connection drops: `navigator.onLine` turns false and `offline` fires. */
function goOffline() {
  Object.defineProperty(window.navigator, "onLine", { value: false, configurable: true });
  act(() => {
    window.dispatchEvent(new Event("offline"));
  });
}

afterEach(() => {
  Reflect.deleteProperty(window.navigator, "onLine");
});

describe("CreditNoteDialog", () => {
  it("blocks submission with no reason, before any request is sent", async () => {
    // Defect this catches: an empty reason reaching the server and
    // bouncing with a generic error instead of being caught client-side
    // before any round trip (`credit-notes` spec's reason requirement).
    mockSession();
    let requestWasSent = false;
    server.use(
      http.post("/api/invoicing/credit-notes", () => {
        requestWasSent = true;
        return HttpResponse.json(CREDIT_NOTE, { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderDialog();

    await user.click(await screen.findByRole("button", { name: "Emitir nota de crédito" }));

    expect(screen.getByText("El motivo es obligatorio.")).toBeInTheDocument();
    expect(requestWasSent).toBe(false);
  });

  it("closes the dialog without issuing when 'Cancelar' is clicked", async () => {
    // Defect this catches: issuing a credit note is irreversible (a
    // Factura is credited once, A6) -- the dialog's only button must
    // not be "Emitir nota de crédito" with no way out.
    mockSession();
    let requestWasSent = false;
    server.use(
      http.post("/api/invoicing/credit-notes", () => {
        requestWasSent = true;
        return HttpResponse.json(CREDIT_NOTE, { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderDialog();

    await screen.findByLabelText(/motivo/i);
    await user.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(requestWasSent).toBe(false);
  });

  it("disables the issue action with its offline message once the connection drops", async () => {
    // Defect this catches: the submit button staying enabled after the
    // connection drops, which would leave the mutation hanging on a
    // `network_error` instead of disabling submit the moment
    // `useOnlineStatus()` flips, matching every other write screen's
    // offline convention (AD-17).
    mockSession();
    renderDialog();

    await screen.findByLabelText(/motivo/i);
    goOffline();

    expect(screen.getByText("Conéctese a internet para emitir una nota de crédito.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Emitir nota de crédito" })).toBeDisabled();
  });

  it("invalidates the invoice, the order's document list, the order detail and settings on success", async () => {
    // Defect this catches: crediting a Factura leaving a stale invoice
    // detail, document list, invoiced-order lock or settings readiness
    // on screen because the mutation forgot to invalidate one of AD-15's
    // query keys.
    mockSession();
    server.use(http.post("/api/invoicing/credit-notes", () => HttpResponse.json(CREDIT_NOTE, { status: 201 })));
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(invoiceQueryKey("w1", "invoice-1"), {});
    queryClient.setQueryData(orderInvoicesQueryKey("w1", "order-1"), []);
    queryClient.setQueryData(workOrderQueryKey("w1", "order-1"), {});
    queryClient.setQueryData(invoicingSettingsQueryKey("w1"), {});
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <CreditNoteDialog open orderId="order-1" invoiceId="invoice-1" onClose={() => {}} />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await user.type(await screen.findByLabelText(/motivo/i), "Datos del comprador incorrectos");
    await user.click(screen.getByRole("button", { name: "Emitir nota de crédito" }));

    await waitFor(() => {
      expect(queryClient.getQueryState(invoiceQueryKey("w1", "invoice-1"))?.isInvalidated).toBe(true);
    });
    expect(queryClient.getQueryState(orderInvoicesQueryKey("w1", "order-1"))?.isInvalidated).toBe(true);
    expect(queryClient.getQueryState(workOrderQueryKey("w1", "order-1"))?.isInvalidated).toBe(true);
    expect(queryClient.getQueryState(invoicingSettingsQueryKey("w1"))?.isInvalidated).toBe(true);
  });
});

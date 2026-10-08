import { afterEach, describe, expect, it } from "vitest";
import { useState } from "react";
import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes, useParams } from "react-router";

import { renderWithQueryClient } from "../../../test/render";
import { server } from "../../../test/server";
import type { CustomerOut } from "../../customers/api";
import type { WorkOrderOut } from "../../workorders/api";
import { IssueInvoiceDialog } from "./IssueInvoiceDialog";

const CUSTOMER: CustomerOut = {
  id: "c1",
  full_name: "María Hernández",
  phone: "98765432",
  phone_is_mobile: true,
  notes: null,
  billing_name: null,
  rtn: null,
  archived_at: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const ORDER: WorkOrderOut = {
  id: "order-1",
  number: 42,
  status: "completed",
  allowed_transitions: ["delivered"],
  lines_editable: true,
  active_invoice: null,
  vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
  customer: { id: "c1", full_name: "María Hernández", phone: "98765432", phone_is_mobile: true },
  complaint: null,
  odometer_km: null,
  notes: null,
  lines: [],
  total_cents: 50000,
  payments: [],
  paid_cents: 0,
  balance_cents: 50000,
  accepts_payments: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  approved_at: null,
  started_at: null,
  completed_at: "2026-01-01T00:00:00Z",
  delivered_at: null,
  cancelled_at: null,
};

/** No readiness warning by default: `IssueInvoiceDialog` always reads this (the same query `InvoiceSection` already triggers), even in tests that do not exercise AD-18's warning line. */
const READY_NO_WARNING_SETTINGS = {
  profile: null,
  codes_locked: false,
  ranges: [],
  documents: [
    { document_type: "01", ready: true, blocked_reason: null, active_range_id: "range-1", next_number: "001-001-01-00000001", warnings: [] },
  ],
};

function mockCustomerAndSession(customerOverrides: Partial<CustomerOut> = {}) {
  server.use(
    http.get("/api/auth/me", () =>
      HttpResponse.json({
        user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
        workshop: { id: "w1", name: "Taller Ana" },
      }),
    ),
    http.get("/api/customers/c1", () => HttpResponse.json({ ...CUSTOMER, ...customerOverrides })),
    http.get("/api/invoicing/settings", () => HttpResponse.json(READY_NO_WARNING_SETTINGS)),
  );
}

function renderDialog(order: WorkOrderOut = ORDER) {
  return renderWithQueryClient(
    <MemoryRouter>
      <IssueInvoiceDialog open order={order} onClose={() => {}} />
    </MemoryRouter>,
  );
}

function InvoiceDetailProbe() {
  const { orderId, invoiceId } = useParams<{ orderId: string; invoiceId: string }>();
  return <p>Invoice detail probe: {orderId}/{invoiceId}</p>;
}

function renderDialogWithNavigation(order: WorkOrderOut = ORDER) {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/dialog"]}>
      <Routes>
        <Route path="/dialog" element={<IssueInvoiceDialog open order={order} onClose={() => {}} />} />
        <Route path="/ordenes/:orderId/factura/:invoiceId" element={<InvoiceDetailProbe />} />
      </Routes>
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

describe("IssueInvoiceDialog", () => {
  it("prefills the buyer fields from the customer's billing data, editable before submit", async () => {
    // Defect this catches: the dialog defaulting to empty buyer fields
    // instead of the customer's own billing name/RTN (`fiscal-invoices`
    // spec's prefill rule), forcing a mechanic to retype data the app
    // already has on every single invoice.
    mockCustomerAndSession({ billing_name: "María Hernández S. de R.L.", rtn: "08011990123456" });
    renderDialog();

    // Waits for the prefill itself to land (an async customer fetch), not
    // just for the field to exist -- it mounts blank before that resolves.
    const nameField = await screen.findByDisplayValue("María Hernández S. de R.L.");
    expect(screen.getByLabelText("RTN")).toHaveValue("08011990123456");

    const user = userEvent.setup();
    await user.clear(nameField);
    await user.type(nameField, "Otro nombre");
    expect(nameField).toHaveValue("Otro nombre");
  });

  it("blocks submit until both name and RTN are filled once the total is at or above the identification threshold", async () => {
    // Defect this catches: the client-side AD-11 mirror letting a submit
    // through with only an RTN and no name for a high-value order, which
    // the server would reject anyway -- the mechanic should see the block
    // before that round trip, not after.
    mockCustomerAndSession(); // no billing data: name prefills from full_name, RTN stays blank
    let issueRequestWasSent = false;
    server.use(
      http.post("/api/invoicing/invoices", () => {
        issueRequestWasSent = true;
        return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
      }),
    );
    const user = userEvent.setup();
    renderDialog({ ...ORDER, total_cents: 1_500_000 });

    // Waits for the prefill (name falls back to the customer's full name)
    // to land before clearing it, so the clear is not silently overwritten
    // by the prefill landing a tick later.
    const nameField = await screen.findByDisplayValue("María Hernández");
    await user.clear(nameField);
    await user.type(screen.getByLabelText("RTN"), "08011990123456");
    await user.click(screen.getByRole("button", { name: "Emitir factura" }));

    expect(screen.getByText("El nombre es obligatorio.")).toBeInTheDocument();
    expect(issueRequestWasSent).toBe(false);
  });

  it("sends exactly one request with one client-generated id on a double click", async () => {
    // Defect this catches: a double-tap on "Emitir factura" (a slow
    // connection, an impatient mechanic) issuing the Factura twice, or
    // issuing it with two different client ids that would defeat the
    // server's own idempotent-replay check.
    mockCustomerAndSession();
    const seenIds: string[] = [];
    let resolveRequest: (() => void) | undefined;
    server.use(
      http.post("/api/invoicing/invoices", async ({ request }) => {
        const body = (await request.json()) as { id: string };
        seenIds.push(body.id);
        // Holds the response open so the mutation stays pending long
        // enough to deterministically attempt a second click while it is
        // in flight, instead of racing React's own re-render.
        await new Promise<void>((resolve) => {
          resolveRequest = resolve;
        });
        return HttpResponse.json({ id: "invoice-1", number: "001-001-01-00000001" }, { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderDialog();

    const submitButton = await screen.findByRole("button", { name: "Emitir factura" });
    await user.click(submitButton);
    await waitFor(() => expect(submitButton).toBeDisabled());
    await user.click(submitButton);
    resolveRequest?.();

    await waitFor(() => expect(seenIds.length).toBe(1));
  });

  it("navigates to the new Factura's own detail screen once it is issued", async () => {
    // Defect this catches: a successful issuance leaving the mechanic
    // stuck on the same dialog with no way to reach the new Factura, or
    // navigating to the wrong invoice id.
    mockCustomerAndSession();
    server.use(
      http.post("/api/invoicing/invoices", () =>
        HttpResponse.json({ id: "invoice-1", number: "001-001-01-00000001" }, { status: 201 }),
      ),
    );
    const user = userEvent.setup();
    renderDialogWithNavigation();

    await user.click(await screen.findByRole("button", { name: "Emitir factura" }));

    expect(await screen.findByText("Invoice detail probe: order-1/invoice-1")).toBeInTheDocument();
  });

  it("shows the range-exhausted message, not the generic fallback, for a 409 cai_range_exhausted response", async () => {
    // Defect this catches: `getInvoicingErrorMessage`'s map had no entry
    // for `cai_range_exhausted` (nor `cai_range_missing`/`cai_range_expired`),
    // so the dialog fell through to the generic "Ocurrió un error. Intente
    // de nuevo." instead of telling the mechanic to go register a new CAI
    // range -- a defect that specifically a real submit through the dialog
    // exposes, since `copy.ts`'s map is otherwise untested from the seam
    // that actually calls it.
    mockCustomerAndSession();
    server.use(
      http.post("/api/invoicing/invoices", () => HttpResponse.json({ detail: "cai_range_exhausted" }, { status: 409 })),
    );
    const user = userEvent.setup();
    renderDialog();

    await user.click(await screen.findByRole("button", { name: "Emitir factura" }));

    expect(await screen.findByText("El rango de CAI se agotó. Registre uno nuevo.")).toBeInTheDocument();
    expect(screen.queryByText("Ocurrió un error. Intente de nuevo.")).not.toBeInTheDocument();
  });

  it("closes the dialog without issuing when 'Cancelar' is clicked", async () => {
    // Defect this catches: issuing a Factura is irreversible (AD-10's
    // immutable snapshot), yet the dialog's only button was "Emitir
    // factura" -- a mechanic who opened it by mistake had no way out
    // except actually issuing it.
    mockCustomerAndSession();
    let issueRequestWasSent = false;
    server.use(
      http.post("/api/invoicing/invoices", () => {
        issueRequestWasSent = true;
        return HttpResponse.json({ id: "invoice-1", number: "001-001-01-00000001" }, { status: 201 });
      }),
    );
    const user = userEvent.setup();

    function ClosableDialog() {
      const [open, setOpen] = useState(true);
      return <IssueInvoiceDialog open={open} order={ORDER} onClose={() => setOpen(false)} />;
    }
    renderWithQueryClient(
      <MemoryRouter>
        <ClosableDialog />
      </MemoryRouter>,
    );

    await screen.findByLabelText("Nombre o razón social");
    await user.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByLabelText("Nombre o razón social")).not.toBeInTheDocument();
    expect(issueRequestWasSent).toBe(false);
  });

  it("shows a range-warning line without blocking submission when the active range carries one", async () => {
    // Defect this catches: a range that is about to expire or run out of
    // numbers (AD-18) giving the owner no signal until it actually blocks
    // issuance (AD-6) -- by then it is too late to request a new one in
    // time. The warning must inform, never block, a still-valid submit.
    mockCustomerAndSession();
    server.use(
      http.get("/api/invoicing/settings", () =>
        HttpResponse.json({
          ...READY_NO_WARNING_SETTINGS,
          documents: [
            {
              document_type: "01",
              ready: true,
              blocked_reason: null,
              active_range_id: "range-1",
              next_number: "001-001-01-00000001",
              warnings: [{ code: "range_low_numbers", remaining: 10 }],
            },
          ],
        }),
      ),
      http.post("/api/invoicing/invoices", () =>
        HttpResponse.json({ id: "invoice-1", number: "001-001-01-00000001" }, { status: 201 }),
      ),
    );
    renderDialog();

    expect(
      await screen.findByText("Factura: Quedan 10 números del rango de CAI. Registre uno nuevo."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Emitir factura" })).not.toBeDisabled();
  });

  it("disables the issue action with its offline message once the connection drops", async () => {
    // Defect this catches: the submit button staying enabled after the
    // connection drops, which would leave the mutation hanging on a
    // `network_error` instead of disabling submit the moment
    // `useOnlineStatus()` flips (matching every other write screen's
    // offline convention, AD-17).
    mockCustomerAndSession();
    renderDialog();

    await screen.findByLabelText("Nombre o razón social");
    goOffline();

    expect(screen.getByText("Conéctese a internet para emitir una factura.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Emitir factura" })).toBeDisabled();
  });
});

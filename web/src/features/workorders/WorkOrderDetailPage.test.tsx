import { afterEach, describe, expect, it } from "vitest";
import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { MemoryRouter, Route, Routes } from "react-router";

import { sessionQueryKey } from "../auth/hooks";
import { renderWithQueryClient } from "../../test/render";
import { server } from "../../test/server";
import { workOrderQueryKey } from "./hooks";
import { WorkOrderDetailPage } from "./WorkOrderDetailPage";
import type { PaymentOut, WorkOrderOut } from "./api";

const SESSION = {
  user: { id: "u1", full_name: "Ana Pérez", phone: "99998888", role: "owner" },
  workshop: { id: "w1", name: "Taller Ana" },
};

const ORDER: WorkOrderOut = {
  id: "order-1",
  number: 42,
  status: "quote",
  allowed_transitions: ["approved", "cancelled"],
  lines_editable: true,
  active_invoice: null,
  vehicle: { id: "v1", vehicle_type: "car", make: "Toyota", model: "Corolla", year: 2015, plate: "HAB1234" },
  customer: { id: "c1", full_name: "María Hernández", phone: "98765432", phone_is_mobile: true },
  complaint: "Ruido en motor",
  odometer_km: 45000,
  notes: null,
  lines: [
    {
      id: "line-1",
      kind: "labor",
      item_id: null,
      description: "Cambio de aceite",
      quantity: 1,
      unit_price_cents: 50000,
      line_total_cents: 50000,
      stock_posted_quantity: 0,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  ],
  total_cents: 50000,
  payments: [],
  paid_cents: 0,
  balance_cents: 50000,
  accepts_payments: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  approved_at: null,
  started_at: null,
  completed_at: null,
  delivered_at: null,
  cancelled_at: null,
};

const PAYMENT: PaymentOut = {
  id: "payment-1",
  amount_cents: 20000,
  method: "cash",
  note: null,
  paid_at: "2026-01-02T00:00:00Z",
  voided_at: null,
  void_reason: null,
};

/** Unlike `ORDER` (`quote`, no payments allowed), `approved` accepts payments and already carries one, for the payment/void tests below. */
const PAYABLE_ORDER: WorkOrderOut = {
  ...ORDER,
  status: "approved",
  allowed_transitions: ["in_progress", "cancelled"],
  payments: [PAYMENT],
  paid_cents: 20000,
  balance_cents: 30000,
  accepts_payments: true,
};

/** `InvoiceSection` always reads this; every test needs a response, even one that stays hidden with no fiscal profile (its own previous, pre-invoicing default). */
const NO_FISCAL_PROFILE_SETTINGS = {
  profile: null,
  codes_locked: false,
  ranges: [],
  documents: [
    { document_type: "01", ready: false, blocked_reason: "fiscal_profile_missing", active_range_id: null, next_number: null },
  ],
};

const FISCAL_PROFILE = {
  rtn: "08019999123456",
  legal_name: "Taller Ana S. de R.L.",
  trade_name: "Taller Ana",
  address: "Col. Kennedy, Tegucigalpa",
  phone: "22223333",
  email: "taller@example.com",
  establishment_code: "001",
  emission_point_code: "001",
  updated_at: "2026-01-01T00:00:00Z",
};

const READY_SETTINGS = {
  ...NO_FISCAL_PROFILE_SETTINGS,
  profile: FISCAL_PROFILE,
  documents: [
    {
      document_type: "01",
      ready: true,
      blocked_reason: null,
      active_range_id: "range-1",
      next_number: "001-001-01-00000001",
    },
  ],
};

function mockSessionAndOrder(order: WorkOrderOut = ORDER) {
  server.use(
    http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
    http.get("/api/work-orders/order-1", () => HttpResponse.json(order)),
    http.get("/api/invoicing/settings", () => HttpResponse.json(NO_FISCAL_PROFILE_SETTINGS)),
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
  // Drops the own-property override from `goOffline`, so jsdom's own
  // `navigator.onLine` getter (always true) applies to the next test.
  Reflect.deleteProperty(window.navigator, "onLine");
});

function renderDetailPage() {
  return renderWithQueryClient(
    <MemoryRouter initialEntries={["/ordenes/order-1"]}>
      <Routes>
        <Route path="/ordenes/:orderId" element={<WorkOrderDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

/**
 * Renders the page over a cache that already holds the session and the
 * order -- what the persister restores from IndexedDB -- while every
 * request fails as it does without a connection.
 */
function renderDetailPageFromCacheWithoutConnection() {
  server.use(
    http.get("/api/auth/me", () => HttpResponse.error()),
    http.get("/api/work-orders/order-1", () => HttpResponse.error()),
    http.get("/api/invoicing/settings", () => HttpResponse.error()),
  );
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  queryClient.setQueryData(sessionQueryKey, SESSION);
  queryClient.setQueryData(workOrderQueryKey("w1", "order-1"), ORDER);

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/ordenes/order-1"]}>
        <Routes>
          <Route path="/ordenes/:orderId" element={<WorkOrderDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("WorkOrderDetailPage", () => {
  it("renders the order's number, vehicle, lines, total, status actions and the WhatsApp share link", async () => {
    // Defect this catches: the read-only detail screen failing to render
    // the order it just fetched, a line's price/total mis-mapped from
    // WorkOrderLineOut, or the status/share actions added this slice
    // never being wired into the page at all.
    mockSessionAndOrder();
    renderDetailPage();

    expect(await screen.findByRole("heading", { name: "Orden #42" })).toBeInTheDocument();
    expect(screen.getByText("Cambio de aceite")).toBeInTheDocument();
    expect(screen.getByText("María Hernández")).toBeInTheDocument();
    expect(screen.getByText("Total").closest("p")).toHaveTextContent("L 500.00");
    expect(screen.getByRole("button", { name: "Aprobar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar orden" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Compartir por WhatsApp" })).toBeInTheDocument();
  });

  it("keeps showing the cached order when refetching it fails for lack of connection", async () => {
    // Defect this catches: a failed refetch flips the order query to
    // "error" while it still holds the cached order; checking the
    // not-found branch before the cached data would make a previously
    // visited order disappear the moment the device goes offline.
    renderDetailPageFromCacheWithoutConnection();

    expect(await screen.findByRole("heading", { name: "Orden #42" })).toBeInTheDocument();
    expect(screen.queryByText("No se encontró la orden.")).not.toBeInTheDocument();
  });

  it("disables the line editor's submit with its offline message once the connection drops while it is open, and sends no request", async () => {
    // Defect this catches: the line editor dialog (`LineEditorDialog`), once
    // already open through this real container, keeps "Guardar línea"
    // enabled after the connection drops -- the add-line mutation would
    // then hang on a `network_error` instead of the dialog disabling
    // submit the moment `useOnlineStatus()` flips, matching every other
    // write screen's offline convention (`design.md`'s AD-17).
    mockSessionAndOrder();
    let lineRequestWasSent = false;
    server.use(
      http.post("/api/work-orders/order-1/lines", () => {
        lineRequestWasSent = true;
        return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
      }),
    );
    const user = userEvent.setup();
    renderDetailPage();

    await user.click(await screen.findByRole("button", { name: "Agregar línea" }));
    const dialog = await screen.findByRole("dialog", { name: "Agregar línea" });

    goOffline();

    expect(
      within(dialog).getByText("Conéctese a internet para editar líneas."),
    ).toBeInTheDocument();
    const saveButton = within(dialog).getByRole("button", { name: "Guardar línea" });
    expect(saveButton).toBeDisabled();

    await user.click(saveButton);
    expect(lineRequestWasSent).toBe(false);
  });

  it("disables the payment form's submit with its offline message once the connection drops", async () => {
    // Defect this catches: the payment form keeps "Registrar pago" enabled
    // after the connection drops, so the mutation would hang on a
    // `network_error` instead of disabling submit the moment
    // `useOnlineStatus()` flips (the `payments` spec's "Payments Require A
    // Live Connection").
    mockSessionAndOrder(PAYABLE_ORDER);
    let paymentRequestWasSent = false;
    server.use(
      http.post("/api/work-orders/order-1/payments", () => {
        paymentRequestWasSent = true;
        return HttpResponse.json({ detail: "unexpected" }, { status: 500 });
      }),
    );
    const user = userEvent.setup();
    renderDetailPage();

    await screen.findByRole("heading", { name: "Orden #42" });
    goOffline();

    expect(screen.getByText("Conéctese a internet para registrar un pago.")).toBeInTheDocument();
    const submitButton = screen.getByRole("button", { name: "Registrar pago" });
    expect(submitButton).toBeDisabled();

    await user.click(submitButton);
    expect(paymentRequestWasSent).toBe(false);
  });

  it("shows the void-payment offline message without requiring the disabled Anular trigger to open the dialog", async () => {
    // Defect this catches: the "Anular" trigger disables itself offline,
    // but the Spanish explanation ("Conéctese a internet para anular un
    // pago.") only rendered inside the confirm dialog that trigger is the
    // only way to open -- so an offline mechanic saw a greyed-out button
    // with no explanation anywhere on screen (the `payments` spec's
    // "Voiding Requires A Live Connection" scenario).
    mockSessionAndOrder(PAYABLE_ORDER);
    renderDetailPage();

    await screen.findByRole("heading", { name: "Orden #42" });
    goOffline();

    expect(screen.getByText("Conéctese a internet para anular un pago.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Anular" })).toBeDisabled();
  });

  it("maps a 409 payment_exceeds_balance to its own Spanish message, not the generic fallback", async () => {
    // Defect this catches: a payment-specific error code falling through
    // to "Ocurrió un error. Intente de nuevo." instead of a message the
    // mechanic can act on.
    mockSessionAndOrder(PAYABLE_ORDER);
    server.use(
      http.post("/api/work-orders/order-1/payments", () =>
        HttpResponse.json({ detail: "payment_exceeds_balance" }, { status: 409 }),
      ),
    );
    const user = userEvent.setup();
    renderDetailPage();

    await user.type(await screen.findByLabelText("Monto del pago"), "9999999");
    await user.click(screen.getByRole("button", { name: "Registrar pago" }));

    expect(await screen.findByText("El monto supera el saldo pendiente.")).toBeInTheDocument();
  });

  it("maps a 409 work_order_not_payable to its own Spanish message, not the generic fallback", async () => {
    mockSessionAndOrder(PAYABLE_ORDER);
    server.use(
      http.post("/api/work-orders/order-1/payments", () =>
        HttpResponse.json({ detail: "work_order_not_payable" }, { status: 409 }),
      ),
    );
    const user = userEvent.setup();
    renderDetailPage();

    await user.type(await screen.findByLabelText("Monto del pago"), "100");
    await user.click(screen.getByRole("button", { name: "Registrar pago" }));

    expect(await screen.findByText("Esta orden no acepta pagos en su estado actual.")).toBeInTheDocument();
  });

  it("maps a 409 payment_id_conflict to its own Spanish message, not the generic fallback", async () => {
    mockSessionAndOrder(PAYABLE_ORDER);
    server.use(
      http.post("/api/work-orders/order-1/payments", () =>
        HttpResponse.json({ detail: "payment_id_conflict" }, { status: 409 }),
      ),
    );
    const user = userEvent.setup();
    renderDetailPage();

    await user.type(await screen.findByLabelText("Monto del pago"), "100");
    await user.click(screen.getByRole("button", { name: "Registrar pago" }));

    expect(await screen.findByText("No se pudo registrar el pago. Intente de nuevo.")).toBeInTheDocument();
  });

  it("maps a 404 payment_not_found to its own Spanish message when voiding a payment", async () => {
    // Defect this catches: `payment_not_found` -- a spec delta this
    // capability adds beyond `specs/payments/spec.md` -- falling through
    // to the generic fallback instead of its own message.
    mockSessionAndOrder(PAYABLE_ORDER);
    server.use(
      http.post("/api/work-orders/order-1/payments/payment-1/void", () =>
        HttpResponse.json({ detail: "payment_not_found" }, { status: 404 }),
      ),
    );
    const user = userEvent.setup();
    renderDetailPage();

    await user.click(await screen.findByRole("button", { name: "Anular" }));
    const dialog = await screen.findByRole("dialog", { name: "Anular pago" });
    await user.type(within(dialog).getByLabelText("Motivo de la anulación"), "Pago duplicado");
    await user.click(within(dialog).getByRole("button", { name: "Sí, anular pago" }));

    expect(await screen.findByText("No se encontró el pago.")).toBeInTheDocument();
  });

  it("links to both receipt layouts once the order is completed", async () => {
    // Defect this catches: the receipt routes existing in router.tsx with
    // no way to reach them from the order detail screen, so a mechanic
    // can never print a receipt for an order that is actually eligible.
    mockSessionAndOrder({ ...ORDER, status: "completed", allowed_transitions: ["delivered"] });
    renderDetailPage();

    expect(await screen.findByRole("heading", { name: "Orden #42" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Recibo 58 mm" })).toHaveAttribute(
      "href",
      "/ordenes/order-1/recibo/58mm",
    );
    expect(screen.getByRole("link", { name: "Recibo carta" })).toHaveAttribute(
      "href",
      "/ordenes/order-1/recibo/carta",
    );
  });

  it("hides the receipt links for an order that is not yet completed or delivered", async () => {
    // Defect this catches: offering a receipt for a quote/in-progress
    // order, which the non-fiscal-receipt spec forbids rendering at all --
    // the link itself would be a dead end showing "no disponible".
    mockSessionAndOrder(ORDER); // status: "quote"
    renderDetailPage();

    expect(await screen.findByRole("heading", { name: "Orden #42" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Recibo 58 mm" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Recibo carta" })).not.toBeInTheDocument();
  });

  it("shows no invoicing action for a workshop with no fiscal profile, the receipt unaffected", async () => {
    // Defect this catches: `InvoiceSection` rendering "Emitir factura" (or
    // crashing on a null profile) for a workshop that never configured
    // fiscal invoicing, which would change every workshop's order screen
    // the moment this capability shipped, not just the ones that opted in
    // (`fiscal-invoices` spec's "A workshop with no fiscal profile sees no
    // Factura action, and the receipt is unaffected").
    mockSessionAndOrder({ ...ORDER, status: "completed", allowed_transitions: ["delivered"] });
    renderDetailPage();

    expect(await screen.findByRole("heading", { name: "Orden #42" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Emitir factura" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Ver factura/ })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Recibo 58 mm" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Recibo carta" })).toBeInTheDocument();
  });

  it("shows 'Emitir factura' ahead of the receipt links for a ready, uninvoiced, eligible order", async () => {
    // Defect this catches: a ready, uninvoiced order never offering a way
    // to issue its Factura, or offering it after the receipt links instead
    // of before them (`fiscal-invoices` spec's "An eligible, uninvoiced
    // order shows the Factura action first").
    mockSessionAndOrder({ ...ORDER, status: "completed", allowed_transitions: ["delivered"] });
    server.use(
      http.get("/api/invoicing/settings", () => HttpResponse.json(READY_SETTINGS)),
      http.get("/api/invoicing/invoices", () => HttpResponse.json([])),
    );
    renderDetailPage();

    expect(await screen.findByRole("heading", { name: "Orden #42" })).toBeInTheDocument();
    const issueButton = await screen.findByRole("button", { name: "Emitir factura" });
    const receiptLink = screen.getByRole("link", { name: "Recibo 58 mm" });
    expect(issueButton.compareDocumentPosition(receiptLink) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByRole("link", { name: "Recibo carta" })).toBeInTheDocument();
  });

  it("links to the issued Factura ahead of the receipt links for an invoiced order", async () => {
    // Defect this catches: an already-invoiced order still offering
    // "Emitir factura" (which would let a mechanic try to double-invoice),
    // or not linking to the Factura at all, or placing it after the
    // receipt links (`fiscal-invoices` spec's "An invoiced order links to
    // the Factura, still ahead of the receipt").
    mockSessionAndOrder({
      ...ORDER,
      status: "completed",
      allowed_transitions: ["delivered"],
      active_invoice: { id: "invoice-1", number: "001-001-01-00000001" },
    });
    server.use(
      http.get("/api/invoicing/settings", () => HttpResponse.json(READY_SETTINGS)),
      http.get("/api/invoicing/invoices", () =>
        HttpResponse.json([
          {
            id: "invoice-1",
            number: "001-001-01-00000001",
            issued_at: "2026-01-02T10:00:00Z",
            total_cents: 50000,
            credited_at: null,
            credit_note: null,
          },
        ]),
      ),
    );
    renderDetailPage();

    expect(await screen.findByRole("heading", { name: "Orden #42" })).toBeInTheDocument();
    const invoiceLink = await screen.findByRole("link", { name: "Ver factura 001-001-01-00000001" });
    expect(invoiceLink).toHaveAttribute("href", "/ordenes/order-1/factura/invoice-1");
    expect(screen.queryByRole("button", { name: "Emitir factura" })).not.toBeInTheDocument();
    const receiptLink = screen.getByRole("link", { name: "Recibo 58 mm" });
    expect(invoiceLink.compareDocumentPosition(receiptLink) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("maps a 409 work_order_invoiced to its own Spanish message when a stale line action is sent", async () => {
    // Defect this catches: the order was fetched while `lines_editable`
    // was still true, then invoiced from another tab before this add-line
    // request landed -- the mechanic's screen still shows "Agregar línea",
    // and the resulting 409 must render the invoicing lock's own message
    // (`work-orders` spec's "Adding a line to an invoiced, completed order
    // is rejected"), not the generic fallback.
    mockSessionAndOrder(ORDER); // lines_editable: true
    server.use(
      http.post("/api/work-orders/order-1/lines", () =>
        HttpResponse.json({ detail: "work_order_invoiced" }, { status: 409 }),
      ),
    );
    const user = userEvent.setup();
    renderDetailPage();

    await user.click(await screen.findByRole("button", { name: "Agregar línea" }));
    const dialog = await screen.findByRole("dialog", { name: "Agregar línea" });
    await user.type(within(dialog).getByLabelText("Descripción"), "Cambio de filtro");
    await user.type(within(dialog).getByLabelText("Precio unitario"), "100");
    await user.click(within(dialog).getByRole("button", { name: "Guardar línea" }));

    expect(
      await screen.findByText("La orden tiene una factura emitida y no se pueden editar sus líneas."),
    ).toBeInTheDocument();
  });
});

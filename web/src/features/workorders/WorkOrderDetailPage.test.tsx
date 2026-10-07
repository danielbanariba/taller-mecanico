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

function mockSessionAndOrder(order: WorkOrderOut = ORDER) {
  server.use(
    http.get("/api/auth/me", () => HttpResponse.json(SESSION)),
    http.get("/api/work-orders/order-1", () => HttpResponse.json(order)),
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
});

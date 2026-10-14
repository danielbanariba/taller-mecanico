import { useState } from "react";
import { useParams } from "react-router";

import { useSession } from "../auth/hooks";
import { ApiError } from "../../shared/api/http";
import { formatCents } from "../../shared/format/money";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { Dialog } from "../../shared/ui/Dialog";
import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { InvoiceSection } from "../invoicing/issue/InvoiceSection";
import { isReceiptEligible } from "./receipt/useReceiptOrder";
import { ShareWhatsAppButton } from "./ShareWhatsAppButton";
import { StatusActions } from "./StatusActions";
import { StatusBadge } from "./StatusBadge";
import { getWorkOrdersErrorMessage, workOrdersCopy } from "./copy";
import { useAddLine, useRecordPayment, useRemoveLine, useUpdateLine, useWorkOrder } from "./hooks";
import { LineEditorDialog, type LineEditorValues } from "./LineEditorDialog";
import { PaymentForm, type PaymentFormValues } from "./payments/PaymentForm";
import { PaymentList } from "./payments/PaymentList";
import { WorkOrderLines } from "./WorkOrderLines";
import type { WorkOrderLineOut } from "./api";

type LineDialogState = { mode: "create" } | { mode: "edit"; line: WorkOrderLineOut } | null;

/**
 * Container: the order detail -- vehicle, customer, lines and total, with
 * the line editor (add/edit/remove), status actions, WhatsApp sharing and
 * payments (record/void) all wired.
 */
export function WorkOrderDetailPage() {
  // Route param name matches `routes.tsx`'s `:orderId` segment (`workOrderRoutes`
  // under `/ordenes` in `app/router.tsx`).
  const { orderId: paramOrderId } = useParams<{ orderId: string }>();
  const orderId = paramOrderId ?? "";
  const isOffline = useOnlineStatus();
  const order = useWorkOrder(orderId);
  const workshopName = useSession().data?.workshop.name ?? "";

  const addLine = useAddLine(orderId);
  const updateLine = useUpdateLine(orderId);
  const removeLine = useRemoveLine(orderId);
  const recordPayment = useRecordPayment(orderId);
  const [lineDialog, setLineDialog] = useState<LineDialogState>(null);
  const [pendingLineId, setPendingLineId] = useState<string | null>(null);
  const [removingLineId, setRemovingLineId] = useState<string | undefined>(undefined);
  // The line pending a remove confirmation (`handleRemoveLine` only opens
  // this dialog; the removal itself fires from `handleRemoveConfirm`, like
  // every other destructive action in this app -- `StatusActions`'s cancel
  // confirm, `PaymentList`'s void confirm).
  const [removeTarget, setRemoveTarget] = useState<WorkOrderLineOut | null>(null);
  // Stable across a failed submit and its retry, like every other
  // client-generated id in this app (`design.md`'s "Create with
  // double-submit"); regenerated only once the payment is actually
  // recorded, so `PaymentForm` remounts via its `key` below and clears
  // its fields for the next payment.
  const [paymentId, setPaymentId] = useState<string>(() => crypto.randomUUID());

  if (order.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // A failed refetch keeps the cached order in `order.data` (e.g. after a
  // reload offline); only the server saying the order is gone replaces it.
  const isNotFound = order.error instanceof ApiError && order.error.status === 404;
  if (isNotFound || !order.data) {
    const errorCode = order.error instanceof ApiError ? order.error.code : "work_order_not_found";
    return (
      <div className="flex flex-col gap-4">
        <Alert variant="error">{getWorkOrdersErrorMessage(errorCode)}</Alert>
        <LinkButton to="/ordenes" variant="secondary">
          {workOrdersCopy.detail.backToList}
        </LinkButton>
      </div>
    );
  }

  const data = order.data;

  const activeLineMutation = lineDialog?.mode === "edit" ? updateLine : addLine;
  const lineErrorMessage =
    activeLineMutation.error instanceof ApiError ? getWorkOrdersErrorMessage(activeLineMutation.error.code) : undefined;
  const removeErrorMessage =
    removeLine.error instanceof ApiError ? getWorkOrdersErrorMessage(removeLine.error.code) : undefined;
  const paymentErrorMessage =
    recordPayment.error instanceof ApiError ? getWorkOrdersErrorMessage(recordPayment.error.code) : undefined;

  function handleRecordPayment(values: PaymentFormValues) {
    recordPayment.mutate(
      { id: paymentId, amount_cents: values.amountCents, method: values.method, note: values.note },
      { onSuccess: () => setPaymentId(crypto.randomUUID()) },
    );
  }

  function handleOpenCreateLine() {
    addLine.reset();
    setPendingLineId(crypto.randomUUID());
    setLineDialog({ mode: "create" });
  }

  function handleOpenEditLine(line: WorkOrderLineOut) {
    updateLine.reset();
    setLineDialog({ mode: "edit", line });
  }

  function handleRemoveLine(line: WorkOrderLineOut) {
    removeLine.reset();
    setRemoveTarget(line);
  }

  function handleRemoveConfirm() {
    if (!removeTarget) {
      return;
    }
    const lineId = removeTarget.id;
    setRemovingLineId(lineId);
    removeLine.mutate(lineId, {
      onSuccess: () => setRemoveTarget(null),
      onSettled: () => setRemovingLineId(undefined),
    });
  }

  function handleLineDialogSubmit(values: LineEditorValues) {
    if (lineDialog?.mode === "edit") {
      updateLine.mutate(
        {
          lineId: lineDialog.line.id,
          payload: {
            description: values.description,
            quantity: values.quantity,
            unit_price_cents: values.unitPriceCents,
          },
        },
        { onSuccess: () => setLineDialog(null) },
      );
      return;
    }
    addLine.mutate(
      {
        id: pendingLineId ?? crypto.randomUUID(),
        kind: values.kind,
        item_id: values.itemId,
        description: values.description,
        quantity: values.quantity,
        unit_price_cents: values.unitPriceCents,
      },
      { onSuccess: () => setLineDialog(null) },
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col items-start gap-1">
        <h1 className="text-2xl font-bold text-brand-primary">{workOrdersCopy.detail.orderTitle(data.number)}</h1>
        <p className="text-sm text-brand-muted-foreground">
          {[data.vehicle.make, data.vehicle.model].filter(Boolean).join(" ")}
          {data.vehicle.plate ? ` · ${data.vehicle.plate}` : ""}
        </p>
        <p className="text-base text-brand-foreground">{data.customer.full_name}</p>
        <StatusBadge status={data.status} />
      </header>

      {data.complaint ? (
        <p className="text-base text-brand-foreground">
          <span className="font-semibold">{workOrdersCopy.detail.complaintLabel}: </span>
          {data.complaint}
        </p>
      ) : null}

      <StatusActions order={data} />
      <ShareWhatsAppButton order={data} workshopName={workshopName} />

      {/* Ahead of the receipt links, never hiding them (`fiscal-invoices`
          spec's "The Factura Action Is Offered First..."). */}
      <InvoiceSection order={data} />

      {isReceiptEligible(data.status) ? (
        <div className="flex flex-col gap-2 sm:flex-row sm:gap-3">
          <LinkButton to={`/ordenes/${orderId}/recibo/58mm`} variant="secondary">
            {workOrdersCopy.receipt.link58mm}
          </LinkButton>
          <LinkButton to={`/ordenes/${orderId}/recibo/carta`} variant="secondary">
            {workOrdersCopy.receipt.linkLetter}
          </LinkButton>
        </div>
      ) : null}

      <section className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-brand-primary">{workOrdersCopy.detail.linesTitle}</h2>
          {data.lines_editable ? (
            <Button
              variant="secondary"
              onClick={handleOpenCreateLine}
              disabled={isOffline}
              fullWidth={false}
              className="px-4"
            >
              {workOrdersCopy.lineEditor.addLine}
            </Button>
          ) : null}
        </div>
        {data.lines_editable && isOffline ? <Alert variant="info">{workOrdersCopy.offline.lineEditDisabled}</Alert> : null}
        <WorkOrderLines
          lines={data.lines}
          editable={data.lines_editable}
          disabled={isOffline}
          onEdit={handleOpenEditLine}
          onRemove={handleRemoveLine}
          removingLineId={removingLineId}
        />
        <p className="flex items-center justify-between text-lg font-bold text-brand-foreground">
          <span>{workOrdersCopy.detail.totalLabel}</span>
          <span>{formatCents(data.total_cents)}</span>
        </p>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-bold text-brand-primary">{workOrdersCopy.payments.sectionTitle}</h2>
        <p className="flex items-center justify-between text-base font-medium text-brand-foreground">
          <span>{workOrdersCopy.payments.paidLabel}</span>
          <span>{formatCents(data.paid_cents)}</span>
        </p>
        <p className="flex items-center justify-between text-base font-semibold text-brand-foreground">
          <span>{data.balance_cents < 0 ? workOrdersCopy.payments.creditLabel : workOrdersCopy.payments.balanceLabel}</span>
          <span>{formatCents(Math.abs(data.balance_cents))}</span>
        </p>
        <PaymentList orderId={orderId} payments={data.payments} />
        {data.accepts_payments && data.balance_cents > 0 ? (
          <PaymentForm
            key={paymentId}
            pending={recordPayment.isPending}
            errorMessage={paymentErrorMessage}
            offline={isOffline}
            balanceCents={data.balance_cents}
            onSubmit={handleRecordPayment}
          />
        ) : (
          <Alert variant="info">
            {data.accepts_payments ? workOrdersCopy.payments.paidInFull : workOrdersCopy.payments.notPayable}
          </Alert>
        )}
      </section>

      <LineEditorDialog
        // Remounts with a fresh `key` for every dialog open -- a new line,
        // a different line to edit, or closed -- so its internal state
        // (which only initializes once, see its own docstring) always
        // starts from this exact `initialLine`/`mode` instead of carrying
        // over the previous line's values.
        key={lineDialog ? (lineDialog.mode === "edit" ? lineDialog.line.id : "new-line") : "closed"}
        open={lineDialog !== null}
        mode={lineDialog?.mode ?? "create"}
        initialLine={lineDialog?.mode === "edit" ? lineDialog.line : undefined}
        pending={lineDialog?.mode === "edit" ? updateLine.isPending : addLine.isPending}
        errorMessage={lineErrorMessage}
        offline={isOffline}
        onClose={() => setLineDialog(null)}
        onSubmit={handleLineDialogSubmit}
      />

      <Dialog
        open={removeTarget !== null}
        title={workOrdersCopy.removeLineConfirm.title}
        onClose={() => setRemoveTarget(null)}
      >
        <div className="flex flex-col gap-4">
          <p className="text-base text-brand-foreground">
            {removeTarget ? workOrdersCopy.removeLineConfirm.body(removeTarget.description) : null}
          </p>
          {isOffline ? <Alert variant="info">{workOrdersCopy.offline.lineEditDisabled}</Alert> : null}
          {removeErrorMessage ? <Alert variant="error">{removeErrorMessage}</Alert> : null}
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setRemoveTarget(null)}>
              {workOrdersCopy.removeLineConfirm.cancel}
            </Button>
            <Button
              variant="destructive"
              onClick={handleRemoveConfirm}
              loading={removeLine.isPending}
              disabled={isOffline || removeLine.isPending}
            >
              {workOrdersCopy.removeLineConfirm.confirm}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

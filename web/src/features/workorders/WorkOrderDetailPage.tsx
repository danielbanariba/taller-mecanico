import { useState } from "react";
import { useParams } from "react-router";

import { ApiError } from "../../shared/api/http";
import { formatCents } from "../../shared/format/money";
import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { Alert } from "../../shared/ui/Alert";
import { Button } from "../../shared/ui/Button";
import { LinkButton } from "../../shared/ui/LinkButton";
import { Spinner } from "../../shared/ui/Spinner";
import { getWorkOrdersErrorMessage, statusLabel, workOrdersCopy } from "./copy";
import { useAddLine, useRemoveLine, useUpdateLine, useWorkOrder } from "./hooks";
import { LineEditorDialog, type LineEditorValues } from "./LineEditorDialog";
import { WorkOrderLines } from "./WorkOrderLines";
import type { WorkOrderLineOut } from "./api";

type LineDialogState = { mode: "create" } | { mode: "edit"; line: WorkOrderLineOut } | null;

/**
 * Container: the order detail -- vehicle, customer, lines and total, with
 * the line editor (add/edit/remove) wired this slice. Status actions,
 * WhatsApp sharing and payments are wired in later slices (S6/P3).
 */
export function WorkOrderDetailPage() {
  // Route param name matches `routes.tsx`'s `:orderId` segment (`workOrderRoutes`
  // under `/ordenes` in `app/router.tsx`).
  const { orderId: paramOrderId } = useParams<{ orderId: string }>();
  const orderId = paramOrderId ?? "";
  const isOffline = useOnlineStatus();
  const order = useWorkOrder(orderId);

  const addLine = useAddLine(orderId);
  const updateLine = useUpdateLine(orderId);
  const removeLine = useRemoveLine(orderId);
  const [lineDialog, setLineDialog] = useState<LineDialogState>(null);
  const [pendingLineId, setPendingLineId] = useState<string | null>(null);
  const [removingLineId, setRemovingLineId] = useState<string | undefined>(undefined);

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
    setRemovingLineId(line.id);
    removeLine.mutate(line.id, { onSettled: () => setRemovingLineId(undefined) });
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
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-brand-primary">{workOrdersCopy.detail.orderTitle(data.number)}</h1>
        <p className="text-sm text-brand-muted-foreground">
          {[data.vehicle.make, data.vehicle.model].filter(Boolean).join(" ")}
          {data.vehicle.plate ? ` · ${data.vehicle.plate}` : ""}
        </p>
        <p className="text-base text-brand-foreground">{data.customer.full_name}</p>
        <p className="text-base font-semibold text-brand-primary">{statusLabel(data.status)}</p>
      </header>

      {data.complaint ? (
        <p className="text-base text-brand-foreground">
          <span className="font-semibold">{workOrdersCopy.detail.complaintLabel}: </span>
          {data.complaint}
        </p>
      ) : null}

      <section className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-brand-primary">{workOrdersCopy.detail.linesTitle}</h2>
          {data.lines_editable ? (
            <Button variant="secondary" onClick={handleOpenCreateLine} disabled={isOffline} className="w-auto px-4">
              {workOrdersCopy.lineEditor.addLine}
            </Button>
          ) : null}
        </div>
        {data.lines_editable && isOffline ? <Alert variant="info">{workOrdersCopy.offline.lineEditDisabled}</Alert> : null}
        {removeErrorMessage ? <Alert variant="error">{removeErrorMessage}</Alert> : null}
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
    </div>
  );
}

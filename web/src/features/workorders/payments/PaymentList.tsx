import { useState } from "react";

import { ApiError } from "../../../shared/api/http";
import { formatCents } from "../../../shared/format/money";
import { useOnlineStatus } from "../../../shared/offline/useOnlineStatus";
import { Alert } from "../../../shared/ui/Alert";
import { Button } from "../../../shared/ui/Button";
import { Dialog } from "../../../shared/ui/Dialog";
import { TextField } from "../../../shared/ui/TextField";
import { getWorkOrdersErrorMessage, paymentMethodLabel, workOrdersCopy } from "../copy";
import { useVoidPayment } from "../hooks";
import type { PaymentOut } from "../api";

export interface PaymentListProps {
  orderId: string;
  payments: PaymentOut[];
}

/**
 * Every recorded payment, in the order the API returns them, each with
 * its own "Anular" action behind a required-reason confirm dialog -- the
 * same shared `Dialog.tsx` pattern `StatusActions` already uses for
 * cancellation (the `payments` spec's "Voiding A Payment Requires A
 * Reason"). A voided payment renders struck through with its reason and
 * never gets another "Anular" action (voiding is one-way, and idempotent
 * at the API, so a retried void of an already-voided payment is never
 * offered a second time from this list).
 */
export function PaymentList({ orderId, payments }: PaymentListProps) {
  const isOffline = useOnlineStatus();
  const voidPayment = useVoidPayment(orderId);
  const [voidTarget, setVoidTarget] = useState<PaymentOut | null>(null);
  const [reason, setReason] = useState("");
  const [touched, setTouched] = useState(false);

  if (payments.length === 0) {
    return <p className="text-base text-brand-muted-foreground">{workOrdersCopy.payments.empty}</p>;
  }

  const errorMessage =
    voidPayment.error instanceof ApiError ? getWorkOrdersErrorMessage(voidPayment.error.code) : undefined;

  function openVoidDialog(payment: PaymentOut) {
    voidPayment.reset();
    setReason("");
    setTouched(false);
    setVoidTarget(payment);
  }

  function handleVoidConfirm() {
    setTouched(true);
    const trimmedReason = reason.trim();
    if (isOffline || trimmedReason.length === 0 || !voidTarget) {
      return;
    }
    voidPayment.mutate(
      { paymentId: voidTarget.id, payload: { reason: trimmedReason } },
      { onSuccess: () => setVoidTarget(null) },
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {isOffline ? <Alert variant="info">{workOrdersCopy.offline.voidPaymentDisabled}</Alert> : null}
      {payments.map((payment) => (
        <div
          key={payment.id}
          className="flex items-center justify-between gap-3 rounded-xl border border-brand-border p-3"
        >
          <div
            className={`flex flex-col gap-0.5 ${
              payment.voided_at ? "text-brand-muted-foreground line-through" : ""
            }`}
          >
            <span className="text-base font-semibold text-brand-foreground">
              {formatCents(payment.amount_cents)} · {paymentMethodLabel(payment.method)}
            </span>
            {payment.note ? <span className="text-sm text-brand-muted-foreground">{payment.note}</span> : null}
            {payment.voided_at ? (
              <span className="text-sm text-brand-muted-foreground">
                {workOrdersCopy.payments.voidedLabel(payment.void_reason ?? "")}
              </span>
            ) : null}
          </div>
          {payment.voided_at ? null : (
            <Button
              variant="destructive"
              onClick={() => openVoidDialog(payment)}
              disabled={isOffline}
              className="w-auto px-4"
            >
              {workOrdersCopy.payments.voidAction}
            </Button>
          )}
        </div>
      ))}

      <Dialog
        open={voidTarget !== null}
        title={workOrdersCopy.payments.voidConfirmTitle}
        onClose={() => setVoidTarget(null)}
      >
        <div className="flex flex-col gap-4">
          <p className="text-base text-brand-foreground">{workOrdersCopy.payments.voidConfirmBody}</p>
          {isOffline ? <Alert variant="info">{workOrdersCopy.offline.voidPaymentDisabled}</Alert> : null}
          {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
          <TextField
            label={workOrdersCopy.payments.voidReasonLabel}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            error={touched && reason.trim().length === 0 ? workOrdersCopy.payments.voidReasonRequired : undefined}
          />
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setVoidTarget(null)}>
              {workOrdersCopy.payments.voidKeep}
            </Button>
            <Button
              variant="destructive"
              onClick={handleVoidConfirm}
              loading={voidPayment.isPending}
              disabled={isOffline || voidPayment.isPending}
            >
              {workOrdersCopy.payments.voidConfirm}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

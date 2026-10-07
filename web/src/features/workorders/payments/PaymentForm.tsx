import { useState } from "react";

import { parseLempirasToCents } from "../../../shared/format/money";
import { Alert } from "../../../shared/ui/Alert";
import { Button } from "../../../shared/ui/Button";
import { Chip } from "../../../shared/ui/Chip";
import { TextField } from "../../../shared/ui/TextField";
import { paymentMethodLabel, workOrdersCopy } from "../copy";
import type { PaymentMethod } from "../api";

const MAX_AMOUNT_CENTS = 1_000_000_000;
const METHOD_OPTIONS: PaymentMethod[] = ["cash", "transfer", "card", "other"];

export interface PaymentFormValues {
  amountCents: number;
  method: PaymentMethod;
  note?: string;
}

export interface PaymentFormProps {
  pending: boolean;
  errorMessage?: string;
  offline: boolean;
  onSubmit: (values: PaymentFormValues) => void;
}

/**
 * Records one payment against the order's current balance. Rendered by
 * `WorkOrderDetailPage` only while the order's `accepts_payments` is
 * true; voiding an existing payment lives in `PaymentList` instead, next
 * to the payment it targets.
 */
export function PaymentForm({ pending, errorMessage, offline, onSubmit }: PaymentFormProps) {
  const [amountText, setAmountText] = useState("");
  const [method, setMethod] = useState<PaymentMethod>("cash");
  const [note, setNote] = useState("");
  const [touched, setTouched] = useState(false);

  const parsedAmount = parseLempirasToCents(amountText);
  const amountInvalid = typeof parsedAmount !== "number" || parsedAmount <= 0 || parsedAmount > MAX_AMOUNT_CENTS;

  function handleSubmit() {
    setTouched(true);
    if (offline || amountInvalid) {
      return;
    }
    onSubmit({
      amountCents: parsedAmount as number,
      method,
      note: note.trim().length > 0 ? note.trim() : undefined,
    });
  }

  return (
    <div className="flex flex-col gap-4">
      {offline ? <Alert variant="info">{workOrdersCopy.offline.paymentDisabled}</Alert> : null}
      {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
      <TextField
        label={workOrdersCopy.payments.amountLabel}
        inputMode="decimal"
        value={amountText}
        onChange={(event) => setAmountText(event.target.value)}
        error={touched && amountInvalid ? workOrdersCopy.payments.amountInvalid : undefined}
      />
      <div className="flex flex-col gap-1.5">
        <span className="text-base font-medium text-brand-foreground">{workOrdersCopy.payments.methodLabel}</span>
        <div className="flex flex-wrap gap-2">
          {METHOD_OPTIONS.map((option) => (
            <Chip key={option} active={method === option} onClick={() => setMethod(option)}>
              {paymentMethodLabel(option)}
            </Chip>
          ))}
        </div>
      </div>
      <TextField
        label={workOrdersCopy.payments.noteLabel}
        value={note}
        onChange={(event) => setNote(event.target.value)}
      />
      <Button onClick={handleSubmit} loading={pending} disabled={offline || pending}>
        {pending ? workOrdersCopy.payments.submitPending : workOrdersCopy.payments.submit}
      </Button>
    </div>
  );
}

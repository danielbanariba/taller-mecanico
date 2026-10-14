import { useState } from "react";

import { formatCents, parseLempirasToCents } from "../../../shared/format/money";
import { Alert } from "../../../shared/ui/Alert";
import { Button } from "../../../shared/ui/Button";
import { Chip } from "../../../shared/ui/Chip";
import { TextField } from "../../../shared/ui/TextField";
import { getWorkOrdersErrorMessage, paymentMethodLabel, workOrdersCopy } from "../copy";
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
  /**
   * The order's current balance due. Cash is the only method a mechanic
   * can receive more than this for (the amount the customer handed
   * over), so it is also what caps a cash payment and what every other
   * method is still rejected against, client-side, before it ever
   * reaches the API.
   */
  balanceCents: number;
  onSubmit: (values: PaymentFormValues) => void;
}

/**
 * Records one payment against the order's current balance. Rendered by
 * `WorkOrderDetailPage` only while the order's `accepts_payments` is
 * true and its balance is still above zero; voiding an existing payment
 * lives in `PaymentList` instead, next to the payment it targets.
 */
export function PaymentForm({ pending, errorMessage, offline, balanceCents, onSubmit }: PaymentFormProps) {
  const [amountText, setAmountText] = useState("");
  const [method, setMethod] = useState<PaymentMethod>("cash");
  const [note, setNote] = useState("");
  const [touched, setTouched] = useState(false);

  const parsedAmount = parseLempirasToCents(amountText);
  const baseAmountInvalid =
    typeof parsedAmount !== "number" || parsedAmount <= 0 || parsedAmount > MAX_AMOUNT_CENTS;
  // Cash means the amount received from the customer, which may be more
  // than the balance (the mechanic gives change back); every other
  // method records what is actually charged, so it stays rejected over
  // the balance the way the API would reject it anyway.
  const exceedsBalance = method !== "cash" && !baseAmountInvalid && (parsedAmount as number) > balanceCents;
  const amountInvalid = baseAmountInvalid || exceedsBalance;
  const changeCents =
    method === "cash" && !baseAmountInvalid && (parsedAmount as number) > balanceCents
      ? (parsedAmount as number) - balanceCents
      : 0;

  // Only one amount message is ever shown: the field's own current
  // validation takes priority and replaces the server's last rejection
  // banner, instead of both appearing together once the field changes.
  const fieldErrorMessage = touched
    ? baseAmountInvalid
      ? workOrdersCopy.payments.amountInvalid
      : exceedsBalance
        ? getWorkOrdersErrorMessage("payment_exceeds_balance")
        : undefined
    : undefined;

  function handleSubmit() {
    setTouched(true);
    if (offline || amountInvalid) {
      return;
    }
    const amount = parsedAmount as number;
    onSubmit({
      amountCents: method === "cash" && amount > balanceCents ? balanceCents : amount,
      method,
      note: note.trim().length > 0 ? note.trim() : undefined,
    });
  }

  return (
    <div className="flex flex-col gap-4">
      {offline ? <Alert variant="info">{workOrdersCopy.offline.paymentDisabled}</Alert> : null}
      {!fieldErrorMessage && errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
      <TextField
        label={workOrdersCopy.payments.amountLabel}
        inputMode="decimal"
        value={amountText}
        onChange={(event) => setAmountText(event.target.value)}
        error={fieldErrorMessage}
        helperText={changeCents > 0 ? workOrdersCopy.payments.changeLabel(formatCents(changeCents)) : undefined}
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

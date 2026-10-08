import { useState } from "react";
import { useNavigate } from "react-router";

import { ApiError } from "../../../shared/api/http";
import { formatCents } from "../../../shared/format/money";
import { useOnlineStatus } from "../../../shared/offline/useOnlineStatus";
import { Alert } from "../../../shared/ui/Alert";
import { Button } from "../../../shared/ui/Button";
import { Dialog } from "../../../shared/ui/Dialog";
import { TextField } from "../../../shared/ui/TextField";
import { useCustomer } from "../../customers/hooks";
import type { WorkOrderOut } from "../../workorders/api";
import { getInvoicingErrorMessage, invoicingCopy } from "../copy";
import { useIssueInvoice } from "../hooks";
import { isBuyerValid } from "./buyer";

export interface IssueInvoiceDialogProps {
  open: boolean;
  order: WorkOrderOut;
  onClose: () => void;
}

/**
 * Issues a Factura for `order`. Unlike `LineEditorDialog`, which stays
 * presentational and lets its container own the mutation, this dialog
 * owns its own customer prefill, mutation and post-issue navigation --
 * there is only ever one place that issues an invoice, so there is no
 * second container to share that logic with.
 *
 * Prefills the buyer from `order.customer`'s own billing data
 * (`useCustomer`), editable before submit. The AD-11 buyer rules are
 * mirrored client-side (`buyer.ts`) to block an invalid submit before a
 * round trip; the server stays authoritative.
 */
export function IssueInvoiceDialog({ open, order, onClose }: IssueInvoiceDialogProps) {
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const customer = useCustomer(order.customer.id);
  const issueInvoice = useIssueInvoice(order.id);
  // Stable across a failed submit and its retry (`design.md`'s "Create
  // with double-submit"), the same convention as every other
  // client-generated id in this app.
  const [invoiceId] = useState(() => crypto.randomUUID());
  const [buyerName, setBuyerName] = useState("");
  const [buyerRtn, setBuyerRtn] = useState("");
  // Tracks which customer's data has already been copied into the (from
  // here on, freely editable) fields above, following React's own
  // "adjusting state during render" pattern instead of an effect -- a
  // `setState` call here, during render, is applied before the browser
  // paints, so it never flashes the still-blank fields first.
  const [prefilledCustomerId, setPrefilledCustomerId] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);

  if (customer.data && prefilledCustomerId !== customer.data.id) {
    setPrefilledCustomerId(customer.data.id);
    setBuyerName(customer.data.billing_name ?? customer.data.full_name);
    setBuyerRtn(customer.data.rtn ?? "");
  }

  const trimmedName = buyerName.trim();
  const trimmedRtn = buyerRtn.trim();
  const buyerIsValid = isBuyerValid({ name: trimmedName, rtn: trimmedRtn }, order.total_cents);
  const showValidationError = touched && !buyerIsValid;

  function handleSubmit() {
    setTouched(true);
    if (isOffline || !buyerIsValid) {
      return;
    }
    issueInvoice.mutate(
      {
        id: invoiceId,
        order_id: order.id,
        buyer_name: trimmedName.length > 0 ? trimmedName : undefined,
        buyer_rtn: trimmedRtn.length > 0 ? trimmedRtn : undefined,
      },
      {
        onSuccess: (invoice) => {
          onClose();
          navigate(`/ordenes/${order.id}/factura/${invoice.id}`);
        },
      },
    );
  }

  const errorMessage =
    issueInvoice.error instanceof ApiError ? getInvoicingErrorMessage(issueInvoice.error.code) : undefined;

  return (
    <Dialog open={open} title={invoicingCopy.issue.dialogTitle} onClose={onClose}>
      <div className="flex flex-col gap-4">
        {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
        {isOffline ? <Alert variant="info">{invoicingCopy.offline.issueInvoiceDisabled}</Alert> : null}
        <p className="text-base text-brand-foreground">
          {invoicingCopy.issue.totalLabel}: {formatCents(order.total_cents)}
        </p>
        <p className="text-sm text-brand-muted-foreground">{invoicingCopy.issue.identificationRequiredNotice}</p>
        <TextField
          label={invoicingCopy.issue.nameLabel}
          name="buyer_name"
          value={buyerName}
          onChange={(event) => setBuyerName(event.target.value)}
          error={showValidationError && trimmedName.length === 0 ? invoicingCopy.issue.nameRequired : undefined}
        />
        <TextField
          label={invoicingCopy.issue.rtnLabel}
          name="buyer_rtn"
          value={buyerRtn}
          onChange={(event) => setBuyerRtn(event.target.value)}
          error={showValidationError && trimmedRtn.length === 0 ? invoicingCopy.issue.rtnRequired : undefined}
        />
        <Button onClick={handleSubmit} loading={issueInvoice.isPending} disabled={isOffline || issueInvoice.isPending}>
          {issueInvoice.isPending ? invoicingCopy.issue.submitPending : invoicingCopy.issue.submit}
        </Button>
      </div>
    </Dialog>
  );
}

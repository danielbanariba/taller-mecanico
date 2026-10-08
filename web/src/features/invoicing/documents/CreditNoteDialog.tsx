import { useState } from "react";
import { useNavigate } from "react-router";

import { ApiError } from "../../../shared/api/http";
import { useOnlineStatus } from "../../../shared/offline/useOnlineStatus";
import { Alert } from "../../../shared/ui/Alert";
import { Button } from "../../../shared/ui/Button";
import { Dialog } from "../../../shared/ui/Dialog";
import { TextArea } from "../../../shared/ui/TextArea";
import { RangeWarnings } from "../settings/RangeWarnings";
import { getInvoicingErrorMessage, invoicingCopy } from "../copy";
import { useInvoicingSettings, useIssueCreditNote } from "../hooks";

export interface CreditNoteDialogProps {
  open: boolean;
  orderId: string;
  invoiceId: string;
  onClose: () => void;
}

/**
 * Confirms and issues a full credit note against an issued Factura
 * (AD-13): the only legal correction v1 supports after issuance. The
 * reason is required before any request is sent; the shared `Dialog`
 * confirm pattern carries an explicit "Cancelar" that closes without
 * issuing, like `IssueInvoiceDialog`.
 */
export function CreditNoteDialog({ open, orderId, invoiceId, onClose }: CreditNoteDialogProps) {
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const issueCreditNote = useIssueCreditNote(orderId, invoiceId);
  // Same readiness `InvoiceSection`/`InvoiceDetailPage` already fetch
  // (deduplicated by TanStack Query): surfaces a `06` range warning
  // (AD-18) right before issuing a correction, without blocking submit.
  const settings = useInvoicingSettings();
  const readiness = settings.data?.documents?.find((document) => document.document_type === "06");
  // Stable across a failed submit and its retry, like every other
  // client-generated id in this app (`design.md`'s "Create with
  // double-submit").
  const [creditNoteId] = useState(() => crypto.randomUUID());
  const [reason, setReason] = useState("");
  const [touched, setTouched] = useState(false);

  const trimmedReason = reason.trim();
  const showValidationError = touched && trimmedReason.length === 0;

  function handleSubmit() {
    setTouched(true);
    if (isOffline || trimmedReason.length === 0) {
      return;
    }
    issueCreditNote.mutate(
      { id: creditNoteId, invoice_id: invoiceId, reason: trimmedReason },
      {
        onSuccess: (creditNote) => {
          onClose();
          navigate(`/ordenes/${orderId}/nota-credito/${creditNote.id}`);
        },
      },
    );
  }

  const errorMessage =
    issueCreditNote.error instanceof ApiError ? getInvoicingErrorMessage(issueCreditNote.error.code) : undefined;

  return (
    <Dialog open={open} title={invoicingCopy.creditNote.dialogTitle} onClose={onClose}>
      <div className="flex flex-col gap-4">
        {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
        {isOffline ? <Alert variant="info">{invoicingCopy.offline.issueCreditNoteDisabled}</Alert> : null}
        {readiness ? <RangeWarnings documents={[readiness]} /> : null}
        <TextArea
          label={invoicingCopy.creditNote.reasonLabel}
          name="reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          error={showValidationError ? invoicingCopy.creditNote.reasonRequired : undefined}
        />
        <div className="flex gap-3">
          <Button variant="secondary" onClick={onClose}>
            {invoicingCopy.creditNote.cancel}
          </Button>
          <Button
            onClick={handleSubmit}
            loading={issueCreditNote.isPending}
            disabled={isOffline || issueCreditNote.isPending}
          >
            {issueCreditNote.isPending ? invoicingCopy.creditNote.submitPending : invoicingCopy.creditNote.submit}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

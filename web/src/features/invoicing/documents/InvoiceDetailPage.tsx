import { useState } from "react";
import { useParams } from "react-router";

import { ApiError } from "../../../shared/api/http";
import { useOnlineStatus } from "../../../shared/offline/useOnlineStatus";
import { Alert } from "../../../shared/ui/Alert";
import { Button } from "../../../shared/ui/Button";
import { LinkButton } from "../../../shared/ui/LinkButton";
import { Spinner } from "../../../shared/ui/Spinner";
import { getInvoicingErrorMessage, invoicingCopy } from "../copy";
import { useInvoice } from "../hooks";
import { CreditNoteDialog } from "./CreditNoteDialog";
import { InvoiceSummary } from "./InvoiceSummary";

/**
 * Container for an issued Factura's own screen, reached from
 * `InvoiceSection`'s "Ver factura" link, or directly offline from the
 * persisted cache (`fiscal-document-print` spec's "A previously fetched
 * document prints offline"). Shows the stored snapshot and links to both
 * print layouts -- never the non-fiscal receipt's own route (AD-16).
 */
export function InvoiceDetailPage() {
  const { orderId: paramOrderId, invoiceId: paramInvoiceId } = useParams<{ orderId: string; invoiceId: string }>();
  const orderId = paramOrderId ?? "";
  const invoiceId = paramInvoiceId ?? "";
  const invoice = useInvoice(invoiceId);
  const isOffline = useOnlineStatus();
  const [creditNoteDialogOpen, setCreditNoteDialogOpen] = useState(false);

  if (invoice.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // A failed refetch keeps the cached invoice in `invoice.data` (e.g. after
  // a reload offline); only the server saying the invoice is gone replaces
  // it, mirroring `WorkOrderDetailPage`'s own not-found handling.
  const isNotFound = invoice.error instanceof ApiError && invoice.error.status === 404;
  if (isNotFound || !invoice.data) {
    const errorCode = invoice.error instanceof ApiError ? invoice.error.code : "fiscal_invoice_not_found";
    return (
      <div className="flex flex-col gap-4">
        <Alert variant="error">{getInvoicingErrorMessage(errorCode)}</Alert>
        <LinkButton to={`/ordenes/${orderId}`} variant="secondary">
          {invoicingCopy.documents.backToOrder}
        </LinkButton>
      </div>
    );
  }

  const data = invoice.data;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-brand-primary">{invoicingCopy.documents.detailTitle(data.number)}</h1>
      <InvoiceSummary invoice={data} />
      {data.credit_note ? (
        <LinkButton to={`/ordenes/${orderId}/nota-credito/${data.credit_note.id}`} variant="secondary">
          {invoicingCopy.creditNote.viewAction(data.credit_note.number)}
        </LinkButton>
      ) : (
        <Button variant="secondary" onClick={() => setCreditNoteDialogOpen(true)} disabled={isOffline}>
          {invoicingCopy.creditNote.issueAction}
        </Button>
      )}
      <div className="flex flex-col gap-2 sm:flex-row sm:gap-3">
        <LinkButton to={`/ordenes/${orderId}/factura/${invoiceId}/58mm`} variant="secondary">
          {invoicingCopy.documents.print58mm}
        </LinkButton>
        <LinkButton to={`/ordenes/${orderId}/factura/${invoiceId}/carta`} variant="secondary">
          {invoicingCopy.documents.printLetter}
        </LinkButton>
      </div>
      <LinkButton to={`/ordenes/${orderId}`} variant="secondary">
        {invoicingCopy.documents.backToOrder}
      </LinkButton>
      {creditNoteDialogOpen ? (
        <CreditNoteDialog
          open={creditNoteDialogOpen}
          orderId={orderId}
          invoiceId={invoiceId}
          onClose={() => setCreditNoteDialogOpen(false)}
        />
      ) : null}
    </div>
  );
}

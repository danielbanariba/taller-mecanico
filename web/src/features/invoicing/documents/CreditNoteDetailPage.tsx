import { useParams } from "react-router";

import { ApiError } from "../../../shared/api/http";
import { formatCents } from "../../../shared/format/money";
import { Alert } from "../../../shared/ui/Alert";
import { LinkButton } from "../../../shared/ui/LinkButton";
import { Spinner } from "../../../shared/ui/Spinner";
import { getInvoicingErrorMessage, invoicingCopy } from "../copy";
import { useCreditNote } from "../hooks";

/**
 * Container for an issued Nota de Crédito's own screen, reached from the
 * credited Factura's detail (`InvoiceDetailPage`), or directly offline
 * from the persisted cache (`fiscal-document-print` spec's "A previously
 * fetched document prints offline", which this screen's own query key
 * already supports). Links to both print layouts (AD-16), never the
 * non-fiscal receipt's own route.
 */
export function CreditNoteDetailPage() {
  const { orderId: paramOrderId, creditNoteId: paramCreditNoteId } = useParams<{
    orderId: string;
    creditNoteId: string;
  }>();
  const orderId = paramOrderId ?? "";
  const creditNoteId = paramCreditNoteId ?? "";
  const creditNote = useCreditNote(creditNoteId);

  if (creditNote.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // A failed refetch keeps the cached credit note in `creditNote.data`
  // (e.g. after a reload offline); only the server saying it is gone
  // replaces it, mirroring `InvoiceDetailPage`'s own not-found handling.
  const isNotFound = creditNote.error instanceof ApiError && creditNote.error.status === 404;
  if (isNotFound || !creditNote.data) {
    const errorCode = creditNote.error instanceof ApiError ? creditNote.error.code : "credit_note_not_found";
    return (
      <div className="flex flex-col gap-4">
        <Alert variant="error">{getInvoicingErrorMessage(errorCode)}</Alert>
        <LinkButton to={`/ordenes/${orderId}`} variant="secondary">
          {invoicingCopy.documents.backToOrder}
        </LinkButton>
      </div>
    );
  }

  const data = creditNote.data;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-brand-primary">
        {invoicingCopy.documents.creditNoteDetailTitle(data.number)}
      </h1>
      <section className="flex flex-col gap-2 rounded-xl border border-brand-border bg-brand-card px-4 py-3">
        <p className="flex items-center justify-between text-base font-semibold text-brand-foreground">
          <span>{invoicingCopy.documents.numberLabel}</span>
          <span>{data.number}</span>
        </p>
        <p className="flex items-center justify-between text-base text-brand-foreground">
          <span>{invoicingCopy.documents.issuedAtLabel}</span>
          <span>{data.issue_date}</span>
        </p>
        <p className="flex items-center justify-between text-base text-brand-foreground">
          <span>{invoicingCopy.documents.buyerLabel}</span>
          <span>{data.buyer_name ?? invoicingCopy.print.finalConsumer}</span>
        </p>
        <p className="flex items-center justify-between text-base text-brand-foreground">
          <span>{invoicingCopy.documents.originalInvoiceLabel}</span>
          <span>{data.original_number}</span>
        </p>
        <p className="text-base text-brand-foreground">
          <span className="font-semibold">{invoicingCopy.documents.reasonLabel}: </span>
          {data.reason}
        </p>
        <p className="flex items-center justify-between text-lg font-bold text-brand-foreground">
          <span>{invoicingCopy.documents.totalLabel}</span>
          <span>{formatCents(data.total_cents)}</span>
        </p>
      </section>
      <div className="flex flex-col gap-2 sm:flex-row sm:gap-3">
        <LinkButton to={`/ordenes/${orderId}/nota-credito/${creditNoteId}/58mm`} variant="secondary">
          {invoicingCopy.documents.print58mm}
        </LinkButton>
        <LinkButton to={`/ordenes/${orderId}/nota-credito/${creditNoteId}/carta`} variant="secondary">
          {invoicingCopy.documents.printLetter}
        </LinkButton>
      </div>
      <LinkButton to={`/ordenes/${orderId}`} variant="secondary">
        {invoicingCopy.documents.backToOrder}
      </LinkButton>
    </div>
  );
}

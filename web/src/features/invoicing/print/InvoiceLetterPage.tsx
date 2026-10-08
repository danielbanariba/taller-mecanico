import { useState } from "react";
import { useParams } from "react-router";

import { ApiError } from "../../../shared/api/http";
import { Alert } from "../../../shared/ui/Alert";
import { LinkButton } from "../../../shared/ui/LinkButton";
import { Spinner } from "../../../shared/ui/Spinner";
import { getInvoicingErrorMessage, invoicingCopy } from "../copy";
import { useInvoice } from "../hooks";
import { InvoiceDocument } from "./InvoiceDocument";
import { LetterPageStyle } from "./LetterPageStyle";
import { PrintActionBar } from "./PrintActionBar";

/**
 * Full-page Factura layout (`fiscal-document-print` spec). Rendered the
 * same way `Invoice58Page` is (AD-16). Both copies print by default, the
 * issuer's own copy starting on its own page (`break-before: page`),
 * unless "Solo original" is checked.
 */
export function InvoiceLetterPage() {
  const { orderId: paramOrderId, invoiceId: paramInvoiceId } = useParams<{ orderId: string; invoiceId: string }>();
  const orderId = paramOrderId ?? "";
  const invoiceId = paramInvoiceId ?? "";
  const invoice = useInvoice(invoiceId);
  const [onlyOriginal, setOnlyOriginal] = useState(false);

  if (invoice.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const isNotFound = invoice.error instanceof ApiError && invoice.error.status === 404;
  if (isNotFound || !invoice.data) {
    const errorCode = invoice.error instanceof ApiError ? invoice.error.code : "fiscal_invoice_not_found";
    return (
      <div className="flex flex-col gap-4 p-6">
        <Alert variant="error">{getInvoicingErrorMessage(errorCode)}</Alert>
        <LinkButton to={`/ordenes/${orderId}`} variant="secondary">
          {invoicingCopy.documents.backToOrder}
        </LinkButton>
      </div>
    );
  }

  const data = invoice.data;

  return (
    <div className="flex flex-col gap-4 p-6">
      <PrintActionBar onlyOriginal={onlyOriginal} onToggleOnlyOriginal={setOnlyOriginal} />
      <LetterPageStyle>
        <InvoiceDocument invoice={data} copy="original" />
        {onlyOriginal ? null : (
          <div className="break-before-page">
            <InvoiceDocument invoice={data} copy="issuer" />
          </div>
        )}
      </LetterPageStyle>
    </div>
  );
}

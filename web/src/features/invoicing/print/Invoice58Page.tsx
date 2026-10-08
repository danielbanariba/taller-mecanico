import { useState } from "react";
import { useParams } from "react-router";

import { ApiError } from "../../../shared/api/http";
import { Alert } from "../../../shared/ui/Alert";
import { LinkButton } from "../../../shared/ui/LinkButton";
import { Spinner } from "../../../shared/ui/Spinner";
import { getInvoicingErrorMessage, invoicingCopy } from "../copy";
import { useInvoice } from "../hooks";
import { InvoiceDocument } from "./InvoiceDocument";
import { PrintActionBar } from "./PrintActionBar";
import { ThermalPageStyle } from "./ThermalPageStyle";

/**
 * 58 mm thermal Factura layout (`fiscal-document-print` spec). Rendered
 * without the app shell (AD-16, wired as a lazy sibling route in
 * `app/router.tsx`), the same way the non-fiscal receipt is, so no
 * navigation chrome ever prints. Both copies print by default, one strip
 * apart, separated by a "cortar aquí" marker, unless "Solo original" is
 * checked.
 */
export function Invoice58Page() {
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
      <div className="flex flex-col gap-4 p-4">
        <Alert variant="error">{getInvoicingErrorMessage(errorCode)}</Alert>
        <LinkButton to={`/ordenes/${orderId}`} variant="secondary">
          {invoicingCopy.documents.backToOrder}
        </LinkButton>
      </div>
    );
  }

  const data = invoice.data;

  return (
    <div className="flex flex-col gap-4 p-4">
      <PrintActionBar onlyOriginal={onlyOriginal} onToggleOnlyOriginal={setOnlyOriginal} />
      <ThermalPageStyle>
        <div className="flex flex-col gap-3">
          <InvoiceDocument invoice={data} copy="original" />
          {onlyOriginal ? null : (
            <>
              <p className="text-center text-xs">{invoicingCopy.print.cutHereLabel}</p>
              <InvoiceDocument invoice={data} copy="issuer" />
            </>
          )}
        </div>
      </ThermalPageStyle>
    </div>
  );
}

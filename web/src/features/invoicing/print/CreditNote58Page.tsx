import { useState } from "react";
import { useParams } from "react-router";

import { ApiError } from "../../../shared/api/http";
import { Alert } from "../../../shared/ui/Alert";
import { LinkButton } from "../../../shared/ui/LinkButton";
import { Spinner } from "../../../shared/ui/Spinner";
import { getInvoicingErrorMessage, invoicingCopy } from "../copy";
import { useCreditNote } from "../hooks";
import { CreditNoteDocument } from "./CreditNoteDocument";
import { PrintActionBar } from "./PrintActionBar";
import { ThermalPageStyle } from "./ThermalPageStyle";

/**
 * 58 mm thermal Nota de Crédito layout (`fiscal-document-print` spec,
 * Phase B requirement). Rendered without the app shell (AD-16, wired as
 * a lazy sibling route in `app/router.tsx`), the same way `Invoice58Page`
 * is. Both copies print by default, one strip apart, separated by a
 * "cortar aquí" marker, unless "Solo original" is checked.
 */
export function CreditNote58Page() {
  const { orderId: paramOrderId, creditNoteId: paramCreditNoteId } = useParams<{
    orderId: string;
    creditNoteId: string;
  }>();
  const orderId = paramOrderId ?? "";
  const creditNoteId = paramCreditNoteId ?? "";
  const creditNote = useCreditNote(creditNoteId);
  const [onlyOriginal, setOnlyOriginal] = useState(false);

  if (creditNote.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const isNotFound = creditNote.error instanceof ApiError && creditNote.error.status === 404;
  if (isNotFound || !creditNote.data) {
    const errorCode = creditNote.error instanceof ApiError ? creditNote.error.code : "credit_note_not_found";
    return (
      <div className="flex flex-col gap-4 p-4">
        <Alert variant="error">{getInvoicingErrorMessage(errorCode)}</Alert>
        <LinkButton to={`/ordenes/${orderId}`} variant="secondary">
          {invoicingCopy.documents.backToOrder}
        </LinkButton>
      </div>
    );
  }

  const data = creditNote.data;

  return (
    <div className="flex flex-col gap-4 p-4">
      <PrintActionBar onlyOriginal={onlyOriginal} onToggleOnlyOriginal={setOnlyOriginal} />
      <ThermalPageStyle>
        <div className="flex flex-col gap-3">
          <CreditNoteDocument creditNote={data} copy="original" layout="thermal" />
          {onlyOriginal ? null : (
            <>
              <p className="text-center text-xs">{invoicingCopy.print.cutHereLabel}</p>
              <CreditNoteDocument creditNote={data} copy="issuer" layout="thermal" />
            </>
          )}
        </div>
      </ThermalPageStyle>
    </div>
  );
}

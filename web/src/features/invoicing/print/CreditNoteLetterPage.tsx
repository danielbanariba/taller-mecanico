import { useState } from "react";
import { useParams } from "react-router";

import { ApiError } from "../../../shared/api/http";
import { Alert } from "../../../shared/ui/Alert";
import { LinkButton } from "../../../shared/ui/LinkButton";
import { Spinner } from "../../../shared/ui/Spinner";
import { getInvoicingErrorMessage, invoicingCopy } from "../copy";
import { useCreditNote } from "../hooks";
import { CreditNoteDocument } from "./CreditNoteDocument";
import { LetterPageStyle } from "./LetterPageStyle";
import { PrintActionBar } from "./PrintActionBar";

/**
 * Full-page Nota de Crédito layout (`fiscal-document-print` spec, Phase
 * B requirement). Rendered the same way `InvoiceLetterPage` is (AD-16).
 * Both copies print by default, the issuer's own copy starting on its
 * own page (`break-before: page`), unless "Solo original" is checked.
 */
export function CreditNoteLetterPage() {
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
      <div className="flex flex-col gap-4 p-6">
        <Alert variant="error">{getInvoicingErrorMessage(errorCode)}</Alert>
        <LinkButton to={`/ordenes/${orderId}`} variant="secondary">
          {invoicingCopy.documents.backToOrder}
        </LinkButton>
      </div>
    );
  }

  const data = creditNote.data;

  return (
    <div className="flex flex-col gap-4 p-6">
      <PrintActionBar onlyOriginal={onlyOriginal} onToggleOnlyOriginal={setOnlyOriginal} />
      <LetterPageStyle>
        <CreditNoteDocument creditNote={data} copy="original" />
        {onlyOriginal ? null : (
          <div className="break-before-page">
            <CreditNoteDocument creditNote={data} copy="issuer" />
          </div>
        )}
      </LetterPageStyle>
    </div>
  );
}

import { documentTypeLabel, getBlockedReasonMessage, invoicingCopy } from "../copy";
import type { DocumentReadinessOut } from "../api";

export interface ReadinessSummaryProps {
  documents: DocumentReadinessOut[];
}

/**
 * Presentational: one line per document type, reporting the exact same
 * readiness `GET /invoicing/settings` computed (AD-3) -- ready with the
 * next number, or the Spanish reason it is still blocked. Phase A only
 * ever reports `"01"`; Phase B adds `"06"`.
 */
export function ReadinessSummary({ documents }: ReadinessSummaryProps) {
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-lg font-bold text-brand-primary">{invoicingCopy.settings.readinessTitle}</h2>
      {documents.map((doc) => (
        <p key={doc.document_type} className="text-base text-brand-foreground">
          <span className="font-semibold">{documentTypeLabel(doc.document_type)}:</span>{" "}
          {doc.ready
            ? invoicingCopy.settings.readyLabel(doc.next_number ?? "")
            : getBlockedReasonMessage(doc.blocked_reason ?? "")}
        </p>
      ))}
    </section>
  );
}

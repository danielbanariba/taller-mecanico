import { Alert } from "../../../shared/ui/Alert";
import { documentTypeLabel, getRangeWarningMessage } from "../copy";
import type { DocumentReadinessOut } from "../api";

export interface RangeWarningsProps {
  documents: DocumentReadinessOut[];
}

/**
 * One Spanish line per active range warning (AD-18), across every
 * document type's own readiness: starting 60 days before a range's fecha
 * límite (Art. 59's 2-month request window), or once its remaining
 * numbers fall at or below the design-fixed threshold. A warning never
 * blocks issuance -- exhaustion and expiry still do that (AD-6) -- it
 * only tells the owner to act before that happens. Renders nothing while
 * no range currently carries a warning.
 */
export function RangeWarnings({ documents }: RangeWarningsProps) {
  const lines = documents.flatMap((doc) =>
    doc.warnings.map((warning) => ({
      key: `${doc.document_type}-${warning.code}`,
      text: `${documentTypeLabel(doc.document_type)}: ${getRangeWarningMessage(warning)}`,
    })),
  );

  if (lines.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-2">
      {lines.map((line) => (
        <Alert key={line.key} variant="info">
          {line.text}
        </Alert>
      ))}
    </div>
  );
}

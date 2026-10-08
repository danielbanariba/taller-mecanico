import { useState, type FormEvent } from "react";

import { Alert } from "../../../shared/ui/Alert";
import { Button } from "../../../shared/ui/Button";
import { TextField } from "../../../shared/ui/TextField";
import { invoicingCopy } from "../copy";
import type { DocumentType } from "../api";

export interface CaiRangeFormValues {
  /** Fixed once a range exists (AD-4); defaults to `"01"` for a new range. */
  documentType: DocumentType;
  cai: string;
  rangeStart: string;
  rangeEnd: string;
  /** `YYYY-MM-DD`, the native `<input type="date">` format. */
  issueDeadline: string;
}

export interface CaiRangeFormSubmitValues {
  documentType: DocumentType;
  cai: string;
  rangeStart: number;
  rangeEnd: number;
  issueDeadline: string;
}

export interface CaiRangeFormProps {
  initialValues?: Partial<CaiRangeFormValues>;
  /** Once a range has allocated a number it is immutable (AD-4): every field is disabled, with an explanation, instead of letting the user submit into a 409. */
  inUse?: boolean;
  onSubmit: (values: CaiRangeFormSubmitValues) => void;
  pending: boolean;
  errorMessage?: string;
  /** Disables submission with an explanation: registering/editing a range needs a connection (`cai-ranges` spec). */
  offline?: boolean;
}

/** Every document type a CAI range can be registered for (A1, Phase B adds `06`). */
const DOCUMENT_TYPES: DocumentType[] = ["01", "06"];

/**
 * Presentational: a CAI range's document type, bounds, CAI, and fecha
 * límite (AD-4). The document type is chosen once, at creation, and
 * fixed forever after (`inUse` disables it exactly like every other
 * field once the range has allocated a number). `rangeStart`/`rangeEnd`
 * are kept as text locally (so the field never fights the user's
 * typing) and parsed to numbers only on submit.
 */
export function CaiRangeForm({
  initialValues,
  inUse = false,
  onSubmit,
  pending,
  errorMessage,
  offline = false,
}: CaiRangeFormProps) {
  const [documentType, setDocumentType] = useState<DocumentType>(initialValues?.documentType ?? "01");
  const [cai, setCai] = useState(initialValues?.cai ?? "");
  const [rangeStart, setRangeStart] = useState(initialValues?.rangeStart ?? "");
  const [rangeEnd, setRangeEnd] = useState(initialValues?.rangeEnd ?? "");
  const [issueDeadline, setIssueDeadline] = useState(initialValues?.issueDeadline ?? "");
  const [touched, setTouched] = useState(false);

  const trimmedCai = cai.trim();
  const trimmedRangeStart = rangeStart.trim();
  const trimmedRangeEnd = rangeEnd.trim();
  const trimmedIssueDeadline = issueDeadline.trim();
  const hasEmptyField =
    trimmedCai.length === 0 ||
    trimmedRangeStart.length === 0 ||
    trimmedRangeEnd.length === 0 ||
    trimmedIssueDeadline.length === 0;

  const disabled = offline || inUse;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setTouched(true);
    if (hasEmptyField || disabled) {
      return;
    }
    onSubmit({
      documentType,
      cai: trimmedCai,
      rangeStart: Number(trimmedRangeStart),
      rangeEnd: Number(trimmedRangeEnd),
      issueDeadline: trimmedIssueDeadline,
    });
  }

  const copy = invoicingCopy.settings.rangeForm;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      {errorMessage ? <Alert variant="error">{errorMessage}</Alert> : null}
      {offline ? <Alert variant="info">{invoicingCopy.offline.rangeWriteDisabled}</Alert> : null}
      {inUse ? <Alert variant="info">{copy.inUseNotice}</Alert> : null}

      <div className="flex flex-col gap-1.5">
        <label htmlFor="document_type" className="text-base font-medium text-brand-foreground">
          {copy.documentTypeLabel}
        </label>
        <select
          id="document_type"
          value={documentType}
          onChange={(event) => setDocumentType(event.target.value as DocumentType)}
          disabled={inUse}
          className="min-h-12 rounded-xl border border-brand-border px-4 text-base text-brand-foreground outline-none focus:ring-2 focus:ring-brand-accent"
        >
          {DOCUMENT_TYPES.map((type) => (
            <option key={type} value={type}>
              {invoicingCopy.settings.documentTypeLabels[type]}
            </option>
          ))}
        </select>
      </div>

      <TextField
        label={copy.caiLabel}
        name="cai"
        value={cai}
        onChange={(event) => setCai(event.target.value)}
        error={touched && trimmedCai.length === 0 ? copy.caiRequired : undefined}
        disabled={inUse}
        required
      />
      <TextField
        label={copy.rangeStartLabel}
        name="range_start"
        type="text"
        inputMode="numeric"
        value={rangeStart}
        onChange={(event) => setRangeStart(event.target.value)}
        error={touched && trimmedRangeStart.length === 0 ? copy.rangeStartRequired : undefined}
        disabled={inUse}
        required
      />
      <TextField
        label={copy.rangeEndLabel}
        name="range_end"
        type="text"
        inputMode="numeric"
        value={rangeEnd}
        onChange={(event) => setRangeEnd(event.target.value)}
        error={touched && trimmedRangeEnd.length === 0 ? copy.rangeEndRequired : undefined}
        disabled={inUse}
        required
      />
      <TextField
        label={copy.issueDeadlineLabel}
        name="issue_deadline"
        type="date"
        value={issueDeadline}
        onChange={(event) => setIssueDeadline(event.target.value)}
        error={touched && trimmedIssueDeadline.length === 0 ? copy.issueDeadlineRequired : undefined}
        disabled={inUse}
        required
      />

      {inUse ? null : (
        <Button type="submit" loading={pending} disabled={disabled || pending}>
          {pending ? copy.submitPending : copy.submit}
        </Button>
      )}
    </form>
  );
}

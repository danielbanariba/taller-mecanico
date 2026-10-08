import { formatCents } from "../../../shared/format/money";
import { formatPhone } from "../../../shared/format/phone";
import { invoicingCopy } from "../copy";
import type { FiscalCreditNoteOut } from "../api";
import { DemoBand } from "./DemoBand";
import type { InvoiceCopyKind, InvoiceDocumentLayout } from "./InvoiceDocument";

export interface CreditNoteDocumentProps {
  creditNote: FiscalCreditNoteOut;
  copy: InvoiceCopyKind;
  layout?: InvoiceDocumentLayout;
}

interface MetaFieldProps {
  label: string;
  value: string;
  layout: InvoiceDocumentLayout;
}

/**
 * Renders "label: value" inline on the letter layout, or the value on
 * its own line below the label on the thermal layout -- the same split
 * `InvoiceDocument`'s own private `MetaField` uses, duplicated here
 * rather than shared (AD-16's "Extracting a shared print helper now" is
 * out of scope for this change).
 */
function MetaField({ label, value, layout }: MetaFieldProps) {
  if (layout === "thermal") {
    return (
      <>
        <p>{label}:</p>
        <p className="whitespace-nowrap font-semibold">{value}</p>
      </>
    );
  }
  return (
    <p>
      {label}: {value}
    </p>
  );
}

/**
 * Formats `issued_at` (a UTC ISO timestamp from the server) as the
 * Honduran local date and time a Nota de Crédito must print (Art.
 * 25-26): always `America/Tegucigalpa`, mirroring `InvoiceDocument`'s
 * own formatter.
 */
const issuedAtFormatter = new Intl.DateTimeFormat("es-HN", {
  timeZone: "America/Tegucigalpa",
  dateStyle: "long",
  timeStyle: "short",
  hour12: false,
});

function formatIssuedAt(isoTimestamp: string): string {
  return issuedAtFormatter.format(new Date(isoTimestamp));
}

/**
 * One full printable copy ("ORIGINAL: CLIENTE" or "COPIA: EMISOR") of an
 * issued Nota de Crédito, rendering every Art. 25-26 mandatory field
 * (design.md's "Printed field map", Nota de Crédito column). Used by
 * both `CreditNote58Page` and `CreditNoteLetterPage`; reuses
 * `ThermalPageStyle`/`LetterPageStyle`/`PrintActionBar`/`DemoBand` from
 * `InvoiceDocument`'s own print primitives, never `ReceiptBody` (AD-16).
 *
 * Unlike a Factura, a credit note has no lines of its own and no
 * exento/exonerado/discount breakdown (it carries only the gravado/ISV
 * split and the total, copied from the credited Factura) and no order
 * reference -- both omitted here, matching the field map exactly.
 */
export function CreditNoteDocument({ creditNote, copy, layout = "letter" }: CreditNoteDocumentProps) {
  const destinationLabel =
    copy === "original" ? invoicingCopy.print.originalLabel : invoicingCopy.print.issuerCopyLabel;

  return (
    <article className="flex flex-col gap-2 break-words">
      <DemoBand />
      <p className="text-center text-xs font-semibold">{destinationLabel}</p>
      <h1 className="text-center text-base font-bold">{invoicingCopy.print.creditNoteDocumentName}</h1>

      <section className="flex flex-col">
        <p className="font-semibold">{creditNote.issuer_legal_name}</p>
        <p>{creditNote.issuer_trade_name}</p>
        <p>RTN: {creditNote.issuer_rtn}</p>
        <p>{creditNote.issuer_address}</p>
        <p>{formatPhone(creditNote.issuer_phone)}</p>
        <p>{creditNote.issuer_email}</p>
      </section>

      <section className="flex flex-col">
        <MetaField label={invoicingCopy.print.numberLabel} value={creditNote.number} layout={layout} />
        <p>CAI: {creditNote.cai}</p>
        <p>
          {invoicingCopy.print.rangeLabel}: {creditNote.range_first_number} - {creditNote.range_last_number}
        </p>
        <MetaField label={invoicingCopy.print.deadlineLabel} value={creditNote.issue_deadline} layout={layout} />
        <MetaField label={invoicingCopy.print.dateLabel} value={creditNote.issue_date} layout={layout} />
        <p>
          {invoicingCopy.print.issuedAtLabel}: {formatIssuedAt(creditNote.issued_at)}
        </p>
      </section>

      <section className="flex flex-col">
        <p>
          {invoicingCopy.print.buyerLabel}: {creditNote.buyer_name ?? invoicingCopy.print.finalConsumer}
        </p>
        {creditNote.buyer_rtn ? <p>RTN: {creditNote.buyer_rtn}</p> : null}
      </section>

      <section className="flex flex-col">
        <p className="font-semibold">{invoicingCopy.print.originalReferenceLabel}</p>
        <p>CAI: {creditNote.original_cai}</p>
        <MetaField
          label={invoicingCopy.print.originalNumberLabel}
          value={creditNote.original_number}
          layout={layout}
        />
        <MetaField
          label={invoicingCopy.print.originalDateLabel}
          value={creditNote.original_issue_date}
          layout={layout}
        />
      </section>

      <section className="flex flex-col">
        <p>
          <span className="font-semibold">{invoicingCopy.print.reasonLabel}: </span>
          {creditNote.reason}
        </p>
      </section>

      <section className="flex flex-col">
        <p>
          {invoicingCopy.print.taxableLabel}: {formatCents(creditNote.taxable_15_cents)}
        </p>
        <p>
          {invoicingCopy.print.isvLabel}: {formatCents(creditNote.isv_15_cents)}
        </p>
        <p className="font-bold">
          {invoicingCopy.print.totalLabel}: {formatCents(creditNote.total_cents)}
        </p>
        <p>{creditNote.total_in_words}</p>
      </section>

      <section className="flex flex-col gap-3 pt-2">
        <p>{invoicingCopy.print.signatureLabel}: ______________________</p>
        <p>{invoicingCopy.print.identificationLabel}: ______________________</p>
      </section>

      <p className="text-center text-xs font-semibold">{destinationLabel}</p>
      <DemoBand />
    </article>
  );
}

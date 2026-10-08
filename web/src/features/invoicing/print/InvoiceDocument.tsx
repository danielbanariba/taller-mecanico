import { formatCents } from "../../../shared/format/money";
import { invoicingCopy } from "../copy";
import type { FiscalInvoiceOut } from "../api";
import { DemoBand } from "./DemoBand";

export type InvoiceCopyKind = "original" | "issuer";

export interface InvoiceDocumentProps {
  invoice: FiscalInvoiceOut;
  copy: InvoiceCopyKind;
}

/**
 * Formats `issued_at` (a UTC ISO timestamp from the server) as the
 * Honduran local date and time a Factura must print (Art. 10-11): always
 * `America/Tegucigalpa`, never the device's own time zone, which would
 * show a different clock hour -- or, past 18:00 local, the wrong day --
 * depending on where the browser happens to be configured.
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
 * issued Factura, rendering every Art. 10-11 mandatory field
 * (design.md's "Printed field map"). Used by both `Invoice58Page` and
 * `InvoiceLetterPage`; never imports the non-fiscal receipt (AD-16).
 *
 * Renders unconditionally from the stored snapshot: zero amounts still
 * go through `formatCents` ("L 0.00"), never a blank or omitted row
 * (`fiscal-document-print` spec's "Zero-Value Fields Print As L 0.00").
 */
export function InvoiceDocument({ invoice, copy }: InvoiceDocumentProps) {
  const destinationLabel =
    copy === "original" ? invoicingCopy.print.originalLabel : invoicingCopy.print.issuerCopyLabel;

  return (
    <article className="flex flex-col gap-2 break-words">
      <DemoBand />
      <p className="text-center text-xs font-semibold">{destinationLabel}</p>
      <h1 className="text-center text-base font-bold">{invoicingCopy.print.documentName}</h1>

      <section className="flex flex-col">
        <p className="font-semibold">{invoice.issuer_legal_name}</p>
        <p>{invoice.issuer_trade_name}</p>
        <p>RTN: {invoice.issuer_rtn}</p>
        <p>{invoice.issuer_address}</p>
        <p>{invoice.issuer_phone}</p>
        <p>{invoice.issuer_email}</p>
      </section>

      <section className="flex flex-col">
        <p>
          {invoicingCopy.print.numberLabel}: {invoice.number}
        </p>
        <p>CAI: {invoice.cai}</p>
        <p>
          {invoicingCopy.print.rangeLabel}: {invoice.range_first_number} - {invoice.range_last_number}
        </p>
        <p>
          {invoicingCopy.print.deadlineLabel}: {invoice.issue_deadline}
        </p>
        <p>
          {invoicingCopy.print.dateLabel}: {invoice.issue_date}
        </p>
        <p>
          {invoicingCopy.print.issuedAtLabel}: {formatIssuedAt(invoice.issued_at)}
        </p>
      </section>

      <section className="flex flex-col">
        <p>
          {invoicingCopy.print.buyerLabel}: {invoice.buyer_name ?? invoicingCopy.print.finalConsumer}
        </p>
        {invoice.buyer_rtn ? <p>RTN: {invoice.buyer_rtn}</p> : null}
      </section>

      <table className="w-full text-left">
        <thead>
          <tr>
            <th>{invoicingCopy.print.descriptionLabel}</th>
            <th>{invoicingCopy.print.quantityLabel}</th>
            <th>{invoicingCopy.print.unitPriceLabel}</th>
          </tr>
        </thead>
        <tbody>
          {invoice.lines.map((line) => (
            <tr key={line.id}>
              <td>{line.description}</td>
              <td>{line.quantity}</td>
              <td>{formatCents(line.unit_price_cents)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <section className="flex flex-col">
        <p>
          {invoicingCopy.print.exemptLabel}: {formatCents(invoice.exempt_cents)}
        </p>
        <p>
          {invoicingCopy.print.exoneratedLabel}: {formatCents(invoice.exonerated_cents)}
        </p>
        <p>
          {invoicingCopy.print.discountLabel}: {formatCents(invoice.discount_cents)}
        </p>
        <p>
          {invoicingCopy.print.taxableLabel}: {formatCents(invoice.taxable_15_cents)}
        </p>
        <p>
          {invoicingCopy.print.isvLabel}: {formatCents(invoice.isv_15_cents)}
        </p>
        <p className="font-bold">
          {invoicingCopy.print.totalLabel}: {formatCents(invoice.total_cents)}
        </p>
        <p>{invoice.total_in_words}</p>
      </section>

      <p className="text-xs">
        {invoicingCopy.print.orderReferenceLabel}: {invoice.order_number}
      </p>

      <p className="text-center text-xs font-semibold">{destinationLabel}</p>
      <DemoBand />
    </article>
  );
}

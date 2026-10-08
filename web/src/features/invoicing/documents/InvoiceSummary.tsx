import { formatCents } from "../../../shared/format/money";
import { invoicingCopy } from "../copy";
import type { FiscalInvoiceOut } from "../api";

export interface InvoiceSummaryProps {
  invoice: FiscalInvoiceOut;
}

/**
 * On-screen (non-printable) summary of an issued Factura: number, issue
 * date, buyer and total. Distinct from `InvoiceDocument`, which renders
 * the full printable snapshot (AD-16).
 */
export function InvoiceSummary({ invoice }: InvoiceSummaryProps) {
  return (
    <section className="flex flex-col gap-2 rounded-xl border border-brand-border bg-brand-card px-4 py-3">
      <p className="flex items-center justify-between text-base font-semibold text-brand-foreground">
        <span>{invoicingCopy.documents.numberLabel}</span>
        <span>{invoice.number}</span>
      </p>
      <p className="flex items-center justify-between text-base text-brand-foreground">
        <span>{invoicingCopy.documents.issuedAtLabel}</span>
        <span>{invoice.issue_date}</span>
      </p>
      <p className="flex items-center justify-between text-base text-brand-foreground">
        <span>{invoicingCopy.documents.buyerLabel}</span>
        <span>{invoice.buyer_name ?? invoicingCopy.print.finalConsumer}</span>
      </p>
      <p className="flex items-center justify-between text-lg font-bold text-brand-foreground">
        <span>{invoicingCopy.documents.totalLabel}</span>
        <span>{formatCents(invoice.total_cents)}</span>
      </p>
    </section>
  );
}

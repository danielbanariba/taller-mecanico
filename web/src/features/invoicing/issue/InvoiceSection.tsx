import { useState, type ReactNode } from "react";

import { useOnlineStatus } from "../../../shared/offline/useOnlineStatus";
import { Button } from "../../../shared/ui/Button";
import { LinkButton } from "../../../shared/ui/LinkButton";
import { CreditNoteDialog } from "../documents/CreditNoteDialog";
import type { WorkOrderOut } from "../../workorders/api";
import { getBlockedReasonMessage, invoicingCopy } from "../copy";
import { useInvoicingSettings, useOrderInvoices } from "../hooks";
import { IssueInvoiceDialog } from "./IssueInvoiceDialog";

export interface InvoiceSectionProps {
  order: WorkOrderOut;
}

/** Statuses `INVOICEABLE` allows issuing a Factura for (`api/.../invoicing/application/use_cases.py`). */
const INVOICEABLE_STATUSES = new Set<WorkOrderOut["status"]>(["completed", "delivered"]);

/**
 * The order's fiscal documents (every past Factura, each with its own
 * credit note once issued) plus whichever action currently applies:
 * "Emitir factura" for an eligible, never-invoiced (or fully credited)
 * order, a blocked-reason link, or "Emitir nota de crédito" for the
 * order's current, non-credited Factura. Rendered ahead of the
 * non-fiscal receipt links on the order detail screen -- never
 * replacing or hiding them (`fiscal-invoices` spec's "The Factura
 * Action Is Offered First On The Order Detail Screen"). Renders
 * nothing for a workshop that never configured a fiscal profile, so
 * opting into this capability never changes any other workshop's
 * screen.
 */
export function InvoiceSection({ order }: InvoiceSectionProps) {
  const isOffline = useOnlineStatus();
  const settings = useInvoicingSettings();
  const hasProfile = Boolean(settings.data?.profile);
  // Only fetched once a profile exists: a workshop that never opted in
  // must never send this request at all.
  const orderInvoices = useOrderInvoices(order.id, hasProfile);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [creditNoteDialogOpen, setCreditNoteDialogOpen] = useState(false);

  if (!hasProfile) {
    return null;
  }

  const invoices = orderInvoices.data ?? [];
  const hasHistory = invoices.length > 0;

  if (!order.active_invoice && !INVOICEABLE_STATUSES.has(order.status) && !hasHistory) {
    return null;
  }

  let action: ReactNode = null;
  if (order.active_invoice) {
    action = (
      <Button variant="secondary" onClick={() => setCreditNoteDialogOpen(true)} disabled={isOffline}>
        {invoicingCopy.creditNote.issueAction}
      </Button>
    );
  } else if (INVOICEABLE_STATUSES.has(order.status)) {
    const readiness = settings.data?.documents.find((document) => document.document_type === "01");
    action = !readiness?.ready ? (
      <LinkButton to="/ordenes/facturacion" variant="secondary">
        {getBlockedReasonMessage(readiness?.blocked_reason ?? "fiscal_profile_missing")}
      </LinkButton>
    ) : (
      <Button variant="secondary" onClick={() => setDialogOpen(true)} disabled={isOffline}>
        {invoicingCopy.issue.issueAction}
      </Button>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {hasHistory ? (
        <ul className="flex flex-col gap-2">
          {invoices.map((invoice) => (
            <li key={invoice.id} className="flex flex-col gap-2 sm:flex-row sm:gap-3">
              <LinkButton to={`/ordenes/${order.id}/factura/${invoice.id}`} variant="secondary">
                {invoicingCopy.issue.viewAction(invoice.number)}
              </LinkButton>
              {invoice.credit_note ? (
                <LinkButton to={`/ordenes/${order.id}/nota-credito/${invoice.credit_note.id}`} variant="secondary">
                  {invoicingCopy.creditNote.viewAction(invoice.credit_note.number)}
                </LinkButton>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
      {action}
      {/* Mounted only while open, unlike `LineEditorDialog`: `IssueInvoiceDialog`
          fetches the customer's own billing data itself (`useCustomer`),
          and that fetch must not fire for every eligible order just
          because its detail screen was opened. */}
      {dialogOpen ? (
        <IssueInvoiceDialog open={dialogOpen} order={order} onClose={() => setDialogOpen(false)} />
      ) : null}
      {order.active_invoice && creditNoteDialogOpen ? (
        <CreditNoteDialog
          open={creditNoteDialogOpen}
          orderId={order.id}
          invoiceId={order.active_invoice.id}
          onClose={() => setCreditNoteDialogOpen(false)}
        />
      ) : null}
    </div>
  );
}

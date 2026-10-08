import { useState } from "react";

import { useOnlineStatus } from "../../../shared/offline/useOnlineStatus";
import { Button } from "../../../shared/ui/Button";
import { LinkButton } from "../../../shared/ui/LinkButton";
import type { WorkOrderOut } from "../../workorders/api";
import { getBlockedReasonMessage, invoicingCopy } from "../copy";
import { useInvoicingSettings } from "../hooks";
import { IssueInvoiceDialog } from "./IssueInvoiceDialog";

export interface InvoiceSectionProps {
  order: WorkOrderOut;
}

/** Statuses `INVOICEABLE` allows issuing a Factura for (`api/.../invoicing/application/use_cases.py`). */
const INVOICEABLE_STATUSES = new Set<WorkOrderOut["status"]>(["completed", "delivered"]);

/**
 * "Emitir factura", or a link to the order's already-issued Factura,
 * rendered ahead of the non-fiscal receipt links on the order detail
 * screen -- never replacing or hiding them (`fiscal-invoices` spec's "The
 * Factura Action Is Offered First On The Order Detail Screen"). Renders
 * nothing for a workshop that never configured a fiscal profile, so
 * opting into this capability never changes any other workshop's screen.
 */
export function InvoiceSection({ order }: InvoiceSectionProps) {
  const isOffline = useOnlineStatus();
  const settings = useInvoicingSettings();
  const [dialogOpen, setDialogOpen] = useState(false);

  if (!settings.data?.profile) {
    return null;
  }

  if (order.active_invoice) {
    return (
      <LinkButton to={`/ordenes/${order.id}/factura/${order.active_invoice.id}`} variant="secondary">
        {invoicingCopy.issue.viewAction(order.active_invoice.number)}
      </LinkButton>
    );
  }

  if (!INVOICEABLE_STATUSES.has(order.status)) {
    return null;
  }

  const readiness = settings.data.documents.find((document) => document.document_type === "01");

  if (!readiness?.ready) {
    return (
      <LinkButton to="/ordenes/facturacion" variant="secondary">
        {getBlockedReasonMessage(readiness?.blocked_reason ?? "fiscal_profile_missing")}
      </LinkButton>
    );
  }

  return (
    <>
      <Button variant="secondary" onClick={() => setDialogOpen(true)} disabled={isOffline}>
        {invoicingCopy.issue.issueAction}
      </Button>
      {/* Mounted only while open, unlike `LineEditorDialog`: this dialog
          fetches the customer's own billing data itself (`useCustomer`),
          and that fetch must not fire for every eligible order just
          because its detail screen was opened. */}
      {dialogOpen ? (
        <IssueInvoiceDialog open={dialogOpen} order={order} onClose={() => setDialogOpen(false)} />
      ) : null}
    </>
  );
}

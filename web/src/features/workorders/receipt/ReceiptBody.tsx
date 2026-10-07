import { formatCents } from "../../../shared/format/money";
import { workOrdersCopy } from "../copy";
import { vehicleLabel } from "../whatsapp";
import type { WorkOrderOut } from "../api";

export interface ReceiptBodyProps {
  order: WorkOrderOut;
}

/**
 * The mandatory "this is not a tax document" label (the `non-fiscal-receipt`
 * spec's "Both Layouts MUST Carry The Mandatory Non-Fiscal Label"), in its
 * own bordered block so it stays visually distinct from the order content
 * around it.
 */
function NonFiscalBanner() {
  return (
    <p className="rounded border border-current px-2 py-1 text-center text-xs font-bold uppercase tracking-wide">
      {workOrdersCopy.receipt.nonFiscalLabel}
    </p>
  );
}

/**
 * Shared content for both printable layouts (`Receipt58Page`,
 * `ReceiptLetterPage`): order number, vehicle, customer, each line with its
 * subtotal, the order total, the paid total and the balance due.
 * `order.paid_cents`/`order.balance_cents` are server-computed from
 * non-voided payments only (`design.md`'s payments section), so this
 * component never has to re-derive that itself. The non-fiscal label
 * repeats at the top and the bottom (AD-19), so it stays visible wherever
 * the content paginates.
 */
export function ReceiptBody({ order }: ReceiptBodyProps) {
  return (
    <div className="flex flex-col gap-3">
      <NonFiscalBanner />

      <header className="flex flex-col gap-0.5">
        <p className="font-bold">{workOrdersCopy.detail.orderTitle(order.number)}</p>
        <p>{vehicleLabel(order)}</p>
        <p>{order.customer.full_name}</p>
      </header>

      <section className="flex flex-col gap-1">
        <p className="font-semibold">{workOrdersCopy.detail.linesTitle}</p>
        <ul className="flex flex-col gap-1">
          {order.lines.map((line) => (
            <li key={line.id} className="flex items-baseline justify-between gap-2">
              <span>
                {line.description} · {line.quantity}
              </span>
              <span>{formatCents(line.line_total_cents)}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="flex flex-col gap-1 border-t border-current pt-2">
        <p className="flex items-center justify-between font-semibold">
          <span>{workOrdersCopy.detail.totalLabel}</span>
          <span>{formatCents(order.total_cents)}</span>
        </p>
        <p className="flex items-center justify-between">
          <span>{workOrdersCopy.payments.paidLabel}</span>
          <span>{formatCents(order.paid_cents)}</span>
        </p>
        <p className="flex items-center justify-between font-semibold">
          <span>
            {order.balance_cents < 0 ? workOrdersCopy.payments.creditLabel : workOrdersCopy.payments.balanceLabel}
          </span>
          <span>{formatCents(Math.abs(order.balance_cents))}</span>
        </p>
      </section>

      <NonFiscalBanner />
    </div>
  );
}

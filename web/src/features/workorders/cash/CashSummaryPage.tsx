import { ApiError } from "../../../shared/api/http";
import { formatCents } from "../../../shared/format/money";
import { useOnlineStatus } from "../../../shared/offline/useOnlineStatus";
import { Alert } from "../../../shared/ui/Alert";
import { Spinner } from "../../../shared/ui/Spinner";
import { getWorkOrdersErrorMessage, paymentMethodLabel, workOrdersCopy } from "../copy";
import { useCashSummary } from "../hooks";
import type { PaymentMethod } from "../api";

const METHODS: readonly PaymentMethod[] = ["cash", "transfer", "card", "other"];

/**
 * Container: today's cash summary by payment method, for reconciling the
 * physical drawer against recorded cash payments (`daily-cash-summary`
 * spec). Always a live read -- never served from the persisted offline
 * cache (`useCashSummary`'s `meta: { persist: false }`) -- so the offline
 * message takes priority over any total still held in memory from
 * before the connection dropped (AD-17).
 */
export function CashSummaryPage() {
  const isOffline = useOnlineStatus();
  const summary = useCashSummary();

  if (isOffline) {
    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-2xl font-bold text-brand-primary">{workOrdersCopy.cashSummary.title}</h1>
        <Alert variant="info">{workOrdersCopy.cashSummary.offlineMessage}</Alert>
      </div>
    );
  }

  if (summary.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (summary.error || !summary.data) {
    const code = summary.error instanceof ApiError ? summary.error.code : "unknown_error";
    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-2xl font-bold text-brand-primary">{workOrdersCopy.cashSummary.title}</h1>
        <Alert variant="error">{getWorkOrdersErrorMessage(code)}</Alert>
      </div>
    );
  }

  const data = summary.data;

  return (
    <div className="flex flex-col gap-4">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-brand-primary">{workOrdersCopy.cashSummary.title}</h1>
        <p className="text-sm text-brand-muted-foreground">{workOrdersCopy.cashSummary.dateLabel(data.date)}</p>
      </header>

      <div className="flex flex-col gap-2 rounded-xl border border-brand-border p-4">
        {METHODS.map((method) => (
          <p key={method} className="flex items-center justify-between text-base font-medium text-brand-foreground">
            <span>{paymentMethodLabel(method)}</span>
            <span>{formatCents(data.totals_cents[method])}</span>
          </p>
        ))}
        <p className="flex items-center justify-between text-lg font-bold text-brand-primary">
          <span>{workOrdersCopy.cashSummary.totalLabel}</span>
          <span>{formatCents(data.total_cents)}</span>
        </p>
      </div>

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-bold text-brand-primary">{workOrdersCopy.cashSummary.paymentsTitle}</h2>
        {data.payments.length === 0 ? (
          <p className="text-base text-brand-muted-foreground">{workOrdersCopy.cashSummary.paymentsEmpty}</p>
        ) : (
          <div className="flex flex-col gap-2">
            {data.payments.map((payment) => (
              <div
                key={payment.id}
                className="flex items-center justify-between gap-3 rounded-xl border border-brand-border p-3"
              >
                <span className="text-sm text-brand-muted-foreground">
                  {workOrdersCopy.detail.orderTitle(payment.order_number)}
                </span>
                <span className="text-base font-semibold text-brand-foreground">
                  {formatCents(payment.amount_cents)} · {paymentMethodLabel(payment.method)}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

import { workOrdersCopy } from "./copy";

/**
 * Phase-1 placeholder for the Órdenes tab. Fetches nothing, so the shell
 * never issues a request to a work-orders endpoint before phase 2 ships
 * it -- the server has none yet.
 */
export function WorkOrdersComingSoon() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-1 rounded-2xl border border-dashed border-brand-border px-4 py-10 text-center">
      <p className="text-lg font-semibold text-brand-foreground">{workOrdersCopy.comingSoon.title}</p>
      <p className="text-base text-brand-muted-foreground">{workOrdersCopy.comingSoon.body}</p>
    </div>
  );
}

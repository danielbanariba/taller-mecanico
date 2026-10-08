import { isDemoBuild } from "../../auth/demoAccount";
import { invoicingCopy } from "../copy";

/**
 * "DEMOSTRACIÓN — SIN VALOR FISCAL" watermark band, rendered only on a
 * demo build (`isDemoBuild()`, AD-17); renders nothing otherwise. Placed
 * at both the top and bottom of each printed copy by `InvoiceDocument`.
 */
export function DemoBand() {
  if (!isDemoBuild()) {
    return null;
  }

  return (
    <p className="rounded border-2 border-dashed border-current px-2 py-1 text-center text-xs font-bold uppercase tracking-wide">
      {invoicingCopy.print.demoWatermark}
    </p>
  );
}

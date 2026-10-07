import { formatCents } from "../../shared/format/money";
import { workOrdersCopy } from "./copy";
import type { WorkOrderOut } from "./api";

/**
 * `https://wa.me/504<8-digit number>?text=<url-encoded summary>`. The
 * customer's phone is already stored as the normalized 8-digit local
 * number (the `customers` capability never stores a country code), so
 * only Honduras' own `504` is prefixed here (`design.md`'s AD-18).
 */
export function buildWhatsAppUrl(localNumber: string, text: string): string {
  return `https://wa.me/504${localNumber}?text=${encodeURIComponent(text)}`;
}

/** Also reused by `receipt/ReceiptBody.tsx` (phase 3), its second consumer. */
export function vehicleLabel(order: WorkOrderOut): string {
  const name = [order.vehicle.make, order.vehicle.model].filter((part): part is string => Boolean(part)).join(" ");
  return order.vehicle.plate ? `${name} · ${order.vehicle.plate}` : name;
}

/**
 * A Spanish summary of the order's number, vehicle, lines and total, for
 * both the `wa.me` link's `text` parameter and the Web Share payload.
 * Every piece of text comes from `copy.ts` (the `whatsapp-sharing`
 * spec's "drawn entirely from copy.ts"); only the join/formatting logic
 * lives here.
 */
export function buildOrderSummary(order: WorkOrderOut, workshopName: string): string {
  const lineTexts = order.lines.map((line) =>
    workOrdersCopy.share.lineItem(line.description, line.quantity, formatCents(line.unit_price_cents)),
  );
  return [
    workOrdersCopy.share.greeting(workshopName),
    workOrdersCopy.share.orderLine(order.number, vehicleLabel(order)),
    "",
    workOrdersCopy.share.linesHeading,
    ...lineTexts,
    "",
    workOrdersCopy.share.totalLine(formatCents(order.total_cents)),
  ].join("\n");
}

/**
 * `true` only where the Web Share API can share files: `canShare` exists
 * and reports support for an actual file (`design.md`'s AD-18 and the
 * `whatsapp-sharing` spec's exact check). A browser can expose
 * `navigator.share` without `canShare`, or `canShare` without file
 * support, so both must be checked.
 */
export function supportsFileShare(): boolean {
  const canShare = (navigator as Navigator & { canShare?: (data?: ShareData) => boolean }).canShare;
  if (typeof canShare !== "function") {
    return false;
  }
  const probeImage = new File([], "probe.png", { type: "image/png" });
  return canShare.call(navigator, { files: [probeImage] });
}

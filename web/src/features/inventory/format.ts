/**
 * Quantity and date formatting for the inventory feature, plus the
 * lempira money helpers re-exported from `shared/format/money` (work
 * orders is now their second consumer, per `design.md`'s "Web
 * architecture per phase" note) so every existing import of this module
 * keeps working unchanged.
 */

export { centsToPlainAmount, formatCents, parseLempirasToCents } from "../../shared/format/money";

/** Upper bound for a typed stock quantity (initial stock, minimum, physical count), matching the API's own bound. */
export const MAX_STOCK = 1_000_000;

/** Parses a non-negative integer typed as a stock quantity; `undefined` for anything else (letters, a sign, a decimal point, or empty). */
export function parseStockQuantity(text: string): number | undefined {
  const trimmed = text.trim();
  if (!/^\d+$/.test(trimmed)) {
    return undefined;
  }
  return Number(trimmed);
}

const dateTimeFormatter = new Intl.DateTimeFormat("es-HN", {
  dateStyle: "medium",
  timeStyle: "short",
});

/** Formats an ISO timestamp the way a mechanic reads it. */
export function formatDateTime(iso: string): string {
  return dateTimeFormatter.format(new Date(iso));
}

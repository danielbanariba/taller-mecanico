/**
 * Client-side mirror of the AD-11 buyer rules (`api/.../domain/buyer.py`'s
 * `resolve_buyer`), so `IssueInvoiceDialog` can block submission before a
 * round trip. The server stays authoritative (`fiscal-invoices` spec): this
 * only saves an avoidable 422/409, it never replaces the real check.
 */

/** L 10,000.00, tax-inclusive (Art. 10-11), matching `IDENTIFICATION_THRESHOLD_CENTS` in `domain/buyer.py`. */
export const IDENTIFICATION_THRESHOLD_CENTS = 1_000_000;

export interface BuyerInput {
  /** Already trimmed. */
  name: string;
  /** Already trimmed. */
  rtn: string;
}

/**
 * Whether `input` is a valid buyer for an invoice totaling `totalCents`:
 * an RTN alone (no name) is always invalid, and a total at or above the
 * threshold requires both fields.
 */
export function isBuyerValid(input: BuyerInput, totalCents: number): boolean {
  const hasName = input.name.length > 0;
  const hasRtn = input.rtn.length > 0;

  if (hasRtn && !hasName) {
    return false;
  }

  if (totalCents >= IDENTIFICATION_THRESHOLD_CENTS && (!hasName || !hasRtn)) {
    return false;
  }

  return true;
}

/**
 * Money and date formatting for the inventory feature. Money is always
 * integer cents of HNL end to end (API contract); these helpers are the
 * only place that converts between that integer and what a human types or
 * reads.
 */

const currencyFormatter = new Intl.NumberFormat("es-HN", {
  style: "currency",
  currency: "HNL",
});

const dateTimeFormatter = new Intl.DateTimeFormat("es-HN", {
  dateStyle: "medium",
  timeStyle: "short",
});

/** Formats integer cents as a Lempiras amount, e.g. `12550` -> "HNL 125.50". */
export function formatCents(cents: number): string {
  return currencyFormatter.format(cents / 100);
}

/** Formats an ISO timestamp the way a mechanic reads it. */
export function formatDateTime(iso: string): string {
  return dateTimeFormatter.format(new Date(iso));
}

/** Formats integer cents as a plain decimal amount for an editable field, e.g. `12550` -> "125.50". */
export function centsToPlainAmount(cents: number): string {
  const sign = cents < 0 ? "-" : "";
  const absoluteCents = Math.abs(cents);
  const whole = Math.trunc(absoluteCents / 100);
  const fraction = String(absoluteCents % 100).padStart(2, "0");
  return `${sign}${whole}.${fraction}`;
}

/**
 * Parses a Lempiras amount typed by the user (e.g. "125.50" or "125") into
 * integer cents without floating-point rounding errors. Returns `null` for
 * empty input and `undefined` for a value that is not a valid amount.
 */
export function parseLempirasToCents(raw: string): number | null | undefined {
  const trimmed = raw.trim();
  if (trimmed === "") {
    return null;
  }
  const match = /^(\d+)(?:[.,](\d{1,2}))?$/.exec(trimmed);
  if (!match) {
    return undefined;
  }
  const [, wholePart, fractionPart = ""] = match;
  const cents = fractionPart.padEnd(2, "0");
  return Number(wholePart) * 100 + Number(cents);
}

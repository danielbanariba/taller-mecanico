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
 * Parses a Lempiras amount typed by the user into integer cents without
 * floating-point rounding errors (only string/digit manipulation below, no
 * division or multiplication on a parsed float). Returns `null` for empty
 * input and `undefined` for a value that is not a valid amount.
 *
 * Accepted shapes: plain digits ("1250"), a single decimal separator (dot
 * or comma) with 1-2 digits ("125.50", "125,50"), and thousands groups of
 * exactly 3 digits joined by commas, with a dot as the decimal separator
 * when both are present ("1,250", "1,250.00", "12,345,678.9") -- this last
 * shape is what `formatCents` (es-HN, comma-grouped) displays, so a user
 * retyping a price exactly as shown must not get "invalid".
 *
 * Ambiguity rule: a comma alone can mean either separator, so the decision
 * is made on digit count, which the two shapes never share -- a single
 * comma followed by exactly 1-2 digits and no dot is the decimal separator
 * ("125,50" -> 125.50); a comma followed by exactly 3 digits is a
 * thousands separator ("1,250" -> 1250). Anything else with a comma
 * (wrong group size, e.g. "1,25,0") is rejected as malformed.
 */
export function parseLempirasToCents(raw: string): number | null | undefined {
  const trimmed = raw.trim();
  if (trimmed === "") {
    return null;
  }

  const groupedWithDecimal = /^\d{1,3}(?:,\d{3})+\.(\d{1,2})$/.exec(trimmed);
  const groupedNoDecimal = /^\d{1,3}(?:,\d{3})+$/.exec(trimmed);
  const commaDecimal = /^\d+,(\d{1,2})$/.exec(trimmed);
  const dotDecimal = /^\d+\.(\d{1,2})$/.exec(trimmed);
  const plainInteger = /^\d+$/.exec(trimmed);

  let wholeDigits: string;
  let fractionDigits: string;

  if (groupedWithDecimal) {
    wholeDigits = trimmed.slice(0, trimmed.indexOf(".")).replace(/,/g, "");
    fractionDigits = groupedWithDecimal[1];
  } else if (groupedNoDecimal) {
    wholeDigits = trimmed.replace(/,/g, "");
    fractionDigits = "";
  } else if (commaDecimal) {
    wholeDigits = trimmed.slice(0, trimmed.indexOf(","));
    fractionDigits = commaDecimal[1];
  } else if (dotDecimal) {
    wholeDigits = trimmed.slice(0, trimmed.indexOf("."));
    fractionDigits = dotDecimal[1];
  } else if (plainInteger) {
    wholeDigits = trimmed;
    fractionDigits = "";
  } else {
    return undefined;
  }

  const cents = fractionDigits.padEnd(2, "0");
  return Number(wholeDigits) * 100 + Number(cents);
}

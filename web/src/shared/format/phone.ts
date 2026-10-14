/**
 * Shows a normalized 8-digit Honduran phone the way it is written locally
 * (`9876-5432`), the same shape the form's helper text suggests. Anything
 * else is returned unchanged rather than guessed at.
 *
 * Moved here from `features/customers/format.ts` once invoicing (phase A)
 * became a second consumer (an issued Factura's own issuer phone), the
 * same precedent that moved the lempira money helpers into
 * `shared/format/money.ts`. `features/customers/format.ts` re-exports
 * this so its existing imports keep working unchanged.
 */
export function formatPhone(phone: string): string {
  return /^\d{8}$/.test(phone) ? `${phone.slice(0, 4)}-${phone.slice(4)}` : phone;
}

const LOCAL_NUMBER_PATTERN = /^\d{8}$/;
const SEPARATOR_PATTERN = /[\s-]/g;
const FIRST_DIGITS = "23456789";

/**
 * Whether `raw` is a valid Honduran phone number, mirroring the API's
 * `PhoneNumber.from_raw` (`api/src/taller/identity/domain/phone_number.py`)
 * exactly: strips spaces and dashes, then a leading `+504` or `504`
 * country code, and checks what remains is 8 digits with a first digit
 * Honduras actually issues (2-9). Used to block an obviously malformed
 * phone before a login/register round trip the API can only reject; never
 * loosen or tighten this relative to the server's own rule.
 */
export function isValidPhone(raw: string): boolean {
  let cleaned = raw.trim().replace(SEPARATOR_PATTERN, "");
  if (cleaned.startsWith("+504")) {
    cleaned = cleaned.slice(4);
  } else if (cleaned.length === 11 && cleaned.startsWith("504")) {
    cleaned = cleaned.slice(3);
  }
  return LOCAL_NUMBER_PATTERN.test(cleaned) && FIRST_DIGITS.includes(cleaned[0]);
}

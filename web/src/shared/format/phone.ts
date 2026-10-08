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

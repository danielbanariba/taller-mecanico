/**
 * Shows a normalized 8-digit Honduran phone the way it is written locally
 * (`9876-5432`, the same shape the form's helper text suggests). Anything
 * else is returned unchanged rather than guessed at.
 */
export function formatPhone(phone: string): string {
  return /^\d{8}$/.test(phone) ? `${phone.slice(0, 4)}-${phone.slice(4)}` : phone;
}

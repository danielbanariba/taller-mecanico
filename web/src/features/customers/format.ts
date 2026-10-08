/**
 * Re-exports the shared Honduran phone formatter, moved to
 * `shared/format/phone` once invoicing became a second consumer, so
 * every existing import of this module keeps working unchanged -- the
 * same pattern `features/inventory/format.ts` uses for the lempira
 * money helpers.
 */
export { formatPhone } from "../../shared/format/phone";

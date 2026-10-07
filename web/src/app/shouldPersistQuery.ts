import type { Query } from "@tanstack/react-query";

/**
 * Keeps every query that still holds data, including one whose latest
 * refetch failed (see `providers.tsx`'s own comment on why that matters
 * for the offline cache) -- except a query explicitly marked `meta: {
 * persist: false }`, the daily cash summary (`design.md`'s AD-17): it
 * must always be a live read, so a stale total surviving a reload and
 * rendering as though it were current would violate the "no stale
 * totals shown as current" requirement.
 *
 * In its own module (not `providers.tsx`) because that file exports the
 * `AppProviders` component: `eslint-plugin-react-refresh` requires a
 * component file to export only components (plus constant literals), so
 * a second function export there would break Fast Refresh.
 */
export function shouldPersistQuery(query: Query): boolean {
  if (query.meta?.persist === false) {
    return false;
  }
  return query.state.data !== undefined;
}

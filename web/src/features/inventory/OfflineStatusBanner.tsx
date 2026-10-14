import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { useCssHeightVariable } from "../../shared/ui/useCssHeightVariable";
import { useOfflineSync } from "./hooks";
import { SyncStatusBanner } from "./SyncStatusBanner";
import { useDelayedFlag } from "./useDelayedFlag";

export interface OfflineStatusBannerProps {
  workshopId: string;
}

/**
 * How long a flush must keep running, or an entry must stay queued, before
 * the "Sincronizando..." / pending-count message shows at all (T3). A
 * flush that finishes before this elapses never shows anything, so a
 * normal, fast sync never flashes the banner on screen -- only the offline
 * message bypasses this delay, since it is worth showing right away.
 */
const SYNC_STATUS_DELAY_MS = 600;

/**
 * Container: wires live online status and the outbox flush to the
 * presentational banner. Rendered as a fixed, toast-like overlay (T3) so
 * it never pushes page content: it used to sit in normal document flow
 * above every route, so each stock tap that queued or flushed a movement
 * pushed the whole page down and back up. `pointer-events-none` on this
 * fixed wrapper keeps it from intercepting taps on whatever sits
 * underneath when there is nothing to show, or around the card's own
 * edges. `SyncStatusBanner` itself stays presentational with no toast
 * styling of its own (it is shared with its own, un-wrapped render in
 * other tests): the inner wrapper below owns the toast look instead --
 * `pointer-events-auto` re-enables taps on the card, `shadow-md` gives it
 * the lift a floating toast needs over page content, and `w-full
 * max-w-sm` matches the fixed width `shadow-md` needs to read as one
 * card. `empty:hidden` drops that wrapper (and its shadow) the instant
 * `SyncStatusBanner` renders nothing, so no bare shadowed box lingers on
 * screen with nothing inside it. `role="status"` on `SyncStatusBanner`'s
 * own element already implies `aria-live="polite"`, so every change here
 * is still announced politely with no extra attribute needed.
 * `print:hidden` (phase 3): this renders inside `RequireSession`, above
 * every route including the receipt layouts, which must never print their
 * own chrome alongside the order content (`design.md`'s AD-19).
 *
 * Anchored at the BOTTOM, just above `BottomNav` (the mobile snackbar
 * pattern) -- not the top. Anchoring it at the top used to land it right
 * over `AppShell`'s header, covering the "Más" button: a QA sweep
 * confirmed that made Caja del día, Facturación, Exportar todo and Cerrar
 * sesión all unreachable while the banner was showing. The offset used to
 * be a hand-copied literal guessing `BottomNav`'s height (`3rem` plus its
 * border); a later QA sweep measured the real nav at ~54.7px, 6px taller
 * than that guess, so the toast sat too close to it. It now reads
 * `--bottom-nav-height`, the nav's own measured height published by
 * `BottomNav` itself (`useCssHeightVariable`) -- `0px` on a route with no
 * nav (a receipt or print layout), so the toast never floats at a stale
 * nav offset there.
 *
 * Also publishes its OWN rendered height as `--sync-toast-height`
 * (`useCssHeightVariable`, on the same fixed wrapper this measures, so it
 * reads `0` the instant `empty:hidden` collapses it): `AppShell`'s `<main>`
 * reads it back to keep its bottom padding clear of both the nav and
 * whatever height the toast currently has -- one line for the offline
 * message, two once a pending change grows it -- instead of a fixed
 * padding that only accounted for the nav.
 */
export function OfflineStatusBanner({ workshopId }: OfflineStatusBannerProps) {
  const isOffline = useOnlineStatus();
  const { pendingCount, syncing, lastErrorMessage } = useOfflineSync(workshopId);
  const showSyncStatus = useDelayedFlag(syncing || pendingCount > 0, SYNC_STATUS_DELAY_MS);
  const toastRef = useCssHeightVariable<HTMLDivElement>("--sync-toast-height");

  return (
    <div
      ref={toastRef}
      className="pointer-events-none fixed inset-x-0 bottom-[calc(var(--bottom-nav-height,0px)+0.75rem)] z-40 flex justify-center px-4 print:hidden"
    >
      <div className="pointer-events-auto w-full max-w-sm rounded-xl shadow-md empty:hidden">
        <SyncStatusBanner
          isOffline={isOffline}
          pendingCount={showSyncStatus ? pendingCount : 0}
          syncing={showSyncStatus && syncing}
          lastErrorMessage={lastErrorMessage}
        />
      </div>
    </div>
  );
}

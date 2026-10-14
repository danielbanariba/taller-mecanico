import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
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
 */
export function OfflineStatusBanner({ workshopId }: OfflineStatusBannerProps) {
  const isOffline = useOnlineStatus();
  const { pendingCount, syncing, lastErrorMessage } = useOfflineSync(workshopId);
  const showSyncStatus = useDelayedFlag(syncing || pendingCount > 0, SYNC_STATUS_DELAY_MS);

  return (
    <div className="pointer-events-none fixed inset-x-0 top-0 z-40 flex justify-center px-4 pt-[max(1rem,env(safe-area-inset-top))] print:hidden">
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

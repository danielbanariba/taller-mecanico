import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { useOfflineSync } from "./hooks";
import { SyncStatusBanner } from "./SyncStatusBanner";

export interface OfflineStatusBannerProps {
  workshopId: string;
}

/**
 * Container: wires live online status and the outbox flush to the
 * presentational banner. `print:hidden` on the wrapper (phase 3): this
 * renders inside `RequireSession`, above every route including the
 * receipt layouts, which must never print their own chrome alongside the
 * order content (`design.md`'s AD-19).
 */
export function OfflineStatusBanner({ workshopId }: OfflineStatusBannerProps) {
  const isOffline = useOnlineStatus();
  const { pendingCount, syncing, lastErrorMessage } = useOfflineSync(workshopId);

  return (
    <div className="print:hidden">
      <SyncStatusBanner isOffline={isOffline} pendingCount={pendingCount} syncing={syncing} lastErrorMessage={lastErrorMessage} />
    </div>
  );
}

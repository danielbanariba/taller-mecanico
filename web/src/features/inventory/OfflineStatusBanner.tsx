import { useOnlineStatus } from "../../shared/offline/useOnlineStatus";
import { useOfflineSync } from "./hooks";
import { SyncStatusBanner } from "./SyncStatusBanner";

export interface OfflineStatusBannerProps {
  workshopId: string;
}

/** Container: wires live online status and the outbox flush to the presentational banner. */
export function OfflineStatusBanner({ workshopId }: OfflineStatusBannerProps) {
  const isOffline = useOnlineStatus();
  const { pendingCount, syncing, lastErrorMessage } = useOfflineSync(workshopId);

  return (
    <SyncStatusBanner isOffline={isOffline} pendingCount={pendingCount} syncing={syncing} lastErrorMessage={lastErrorMessage} />
  );
}

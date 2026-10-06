import { inventoryCopy } from "./copy";

export interface SyncStatusBannerProps {
  isOffline: boolean;
  pendingCount: number;
  syncing: boolean;
  lastErrorMessage?: string;
}

/**
 * Presentational, persistent status strip: offline, how many changes are
 * still queued, syncing, and the last definitive sync error. Renders
 * nothing when there is genuinely nothing to tell the mechanic.
 */
export function SyncStatusBanner({ isOffline, pendingCount, syncing, lastErrorMessage }: SyncStatusBannerProps) {
  if (!isOffline && pendingCount === 0 && !syncing && !lastErrorMessage) {
    return null;
  }

  return (
    <div
      role="status"
      className="flex flex-col gap-0.5 rounded-xl border border-brand-border bg-brand-muted px-4 py-2 text-sm text-brand-foreground"
    >
      {isOffline ? <span className="font-semibold">{inventoryCopy.offline.offlineMessage}</span> : null}
      {pendingCount > 0 ? <span>{inventoryCopy.offline.pendingCount(pendingCount)}</span> : null}
      {syncing ? <span>{inventoryCopy.offline.syncingMessage}</span> : null}
      {lastErrorMessage ? <span className="font-medium text-brand-destructive">{lastErrorMessage}</span> : null}
    </div>
  );
}

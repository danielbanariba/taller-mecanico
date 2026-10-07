import { useSyncExternalStore } from "react";
import { onlineManager } from "@tanstack/react-query";

function subscribe(onChange: () => void): () => void {
  const unsubscribe = onlineManager.subscribe(onChange);
  window.addEventListener("online", onChange);
  window.addEventListener("offline", onChange);
  return () => {
    unsubscribe();
    window.removeEventListener("online", onChange);
    window.removeEventListener("offline", onChange);
  };
}

/**
 * Offline when either source says so. `onlineManager` (TanStack Query's
 * app-wide store, listening for as long as the QueryClient is mounted)
 * remembers the last `online`/`offline` event, so a screen mounted after
 * the connection dropped agrees with screens mounted before it even when
 * `navigator.onLine` has not caught up (T8 saw this in Chromium after a
 * reload). `navigator.onLine` covers the other gap: `onlineManager` starts
 * out "online" on every page load whatever the browser reports, until an
 * event fires.
 */
function getSnapshot(): boolean {
  return !onlineManager.isOnline() || (typeof navigator !== "undefined" && !navigator.onLine);
}

function getServerSnapshot(): boolean {
  return false;
}

/** True while the browser reports no network connection. */
export function useOnlineStatus(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

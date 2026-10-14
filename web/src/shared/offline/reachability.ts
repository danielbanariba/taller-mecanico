import { onlineManager } from "@tanstack/react-query";

/**
 * How often `startProbing` polls `/api/health` while the app believes it is
 * offline. Also probed immediately on window `focus` and on
 * `visibilitychange` to `"visible"`, so returning to the tab (the most
 * common way a mechanic actually notices the connection is back) does not
 * wait out the interval.
 */
export const PROBE_INTERVAL_MS = 10_000;

let intervalId: ReturnType<typeof setInterval> | undefined;
let unsubscribeOnlineManager: (() => void) | undefined;

/**
 * `navigator.onLine` false is a strong "no radio/no link" signal the OS
 * itself reports; a probe would just fail and burn a request for nothing.
 * `onlineManager`'s own default `setup` already attaches the browser's
 * `online` event listener the moment anything subscribes to it (every
 * mounted `useOnlineStatus()` does), so the real reconnection still flips
 * `onlineManager` back on its own once the OS reports a link again --
 * `startProbing`'s own subscription below then tears itself down.
 */
function shouldSkipProbe(): boolean {
  return typeof navigator !== "undefined" && !navigator.onLine;
}

async function probeOnce(): Promise<void> {
  if (shouldSkipProbe()) {
    return;
  }
  try {
    const response = await fetch("/api/health", { cache: "no-store", credentials: "same-origin" });
    if (response.ok) {
      onlineManager.setOnline(true);
    }
    // A non-ok response (e.g. the API up but its database down) leaves
    // `onlineManager` offline and the loop below keeps probing.
  } catch {
    // Still unreachable: keep probing on the next interval tick/focus/visibility event.
  }
}

function handleFocus(): void {
  void probeOnce();
}

function handleVisibilityChange(): void {
  if (document.visibilityState === "visible") {
    void probeOnce();
  }
}

function stopProbing(): void {
  if (intervalId === undefined) {
    return;
  }
  clearInterval(intervalId);
  intervalId = undefined;
  window.removeEventListener("focus", handleFocus);
  document.removeEventListener("visibilitychange", handleVisibilityChange);
  unsubscribeOnlineManager?.();
  unsubscribeOnlineManager = undefined;
}

function startProbing(): void {
  if (intervalId !== undefined) {
    // Already probing: a second failed request while the first probe loop
    // is still running must not start a second, overlapping one.
    return;
  }
  intervalId = setInterval(() => void probeOnce(), PROBE_INTERVAL_MS);
  window.addEventListener("focus", handleFocus);
  document.addEventListener("visibilitychange", handleVisibilityChange);
  // The only way this loop ever stops is `onlineManager` reporting online,
  // whatever restored it -- this module's own successful probe, the
  // browser's real `online` event (via `onlineManager`'s default `setup`),
  // or a test's cleanup calling `setOnline(true)` directly.
  unsubscribeOnlineManager = onlineManager.subscribe(() => {
    if (onlineManager.isOnline()) {
      stopProbing();
    }
  });
}

/**
 * Call this from `QueryCache`/`MutationCache`'s `onError` whenever a request
 * throws `ApiError("network_error")` (`shared/api/http.ts`'s `request`, only
 * thrown when `fetch` itself rejected -- no route to the server). It marks
 * `onlineManager` offline for every `useOnlineStatus()` consumer and starts
 * a bounded reachability probe against `/api/health` to bring it back.
 *
 * Without this, nothing ever corrects `onlineManager` after a transient
 * failure while the browser's own `online`/`offline` events stay silent --
 * which happens whenever `navigator.onLine` was true the whole time (the API
 * restarting mid-deploy, a tunnel hiccup, a phone's mobile data running out
 * without the OS ever reporting "no link"). The app would then report
 * offline, pause every query and mutation, and disable every write form
 * until an unrelated reload, with nothing it could do succeeding to prove
 * the connection is back.
 */
export function reportNetworkError(): void {
  onlineManager.setOnline(false);
  startProbing();
}

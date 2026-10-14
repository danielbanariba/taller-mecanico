import { useState, type ReactNode } from "react";
import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";

import { ApiError } from "../shared/api/http";
import { idbPersister } from "../shared/offline/idbPersister";
import { reportNetworkError } from "../shared/offline/reachability";
import { shouldPersistQuery } from "./shouldPersistQuery";

/**
 * TanStack's `onlineManager` only learns about a connection drop from the
 * browser's own `online`/`offline` events (`useOnlineStatus.ts`'s own
 * comment) -- it starts every page load assuming "online" and never looks
 * at `navigator.onLine` itself. On a cold load that is *already* offline
 * (reopened from the service worker's precache, or DevTools' network
 * throttling set before the reload), neither signal has any reason to be
 * right yet: no transition happened this session for an `offline` event to
 * fire, and `navigator.onLine` can lag behind real connectivity for the
 * same reason (`useOnlineStatus.ts`'s own "T8" case). Every invoicing write
 * surface already gates correctly on `useOnlineStatus()` -- the bug is that
 * nothing ever corrects `onlineManager` in that window, so every consumer
 * reads "online" and renders fully enabled with no offline message, until
 * an unrelated real browser event eventually fires.
 *
 * A failed request is a better signal than either: `request` in
 * `shared/api/http.ts` only throws `ApiError` with code `"network_error"`
 * when `fetch` itself rejected (no route to the server), never for an
 * actual HTTP error response. Catching that here, once, corrects
 * `onlineManager` for every `useOnlineStatus()` consumer in the app the
 * moment the very first request (a background refetch or a write) proves
 * we cannot reach the server -- not only for whichever screen happened to
 * trigger it.
 *
 * Recovery is delegated to `reachability.ts`'s `reportNetworkError`, not
 * done here: a prior version of this comment called itself "deliberately
 * one-directional" and relied on the browser's own `online` event to flip
 * `onlineManager` back -- which never fires when `navigator.onLine` stayed
 * true the whole time (the API restarting mid-deploy, a tunnel hiccup, a
 * phone's mobile data running out). That left the app stuck reporting
 * offline until an unrelated reload, with nothing left that could succeed
 * to prove the connection was back. `reportNetworkError` starts a bounded
 * `/api/health` probe instead, and still never resets the flag from a
 * successful *unrelated* query -- only that dedicated probe (or a genuine
 * browser `online` event) ever calls `onlineManager.setOnline(true)`, so two
 * other requests racing while truly offline can never flap the flag between
 * "online" and "offline" by which one happens to settle last.
 */
function markOfflineOnNetworkError(error: unknown): void {
  if (error instanceof ApiError && error.code === "network_error") {
    reportNetworkError();
  }
}

/**
 * How long a persisted (or in-memory) cache entry is kept. Generous on
 * purpose: a shop may go a week between opening the app, and the point of
 * T6 is that inventory stays readable through that gap. `gcTime` (the
 * in-memory garbage-collection window) is set to at least `maxAge` (the
 * persisted-cache expiry below) -- otherwise a query could be garbage
 * collected from memory before it is ever persisted.
 */
export const PERSISTED_CACHE_MAX_AGE_MS = 1000 * 60 * 60 * 24 * 7;

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({ onError: markOfflineOnNetworkError }),
        mutationCache: new MutationCache({ onError: markOfflineOnNetworkError }),
        defaultOptions: {
          queries: {
            // A 401 from /api/auth/me means "not logged in", not a
            // transient failure, so it must not retry. A network_error
            // (offline) also should not retry: RequireSession reads the
            // cached data straight away instead of waiting out retries.
            retry: false,
            gcTime: PERSISTED_CACHE_MAX_AGE_MS,
          },
        },
      }),
  );

  return (
    <PersistQueryClientProvider
      client={queryClient}
      persistOptions={{
        persister: idbPersister,
        maxAge: PERSISTED_CACHE_MAX_AGE_MS,
        // Busts any cache left over from a previous deploy whose
        // dehydrated shape may not match this build's query keys/shapes.
        // `__APP_VERSION__` (vite.config.ts) carries a per-build id, not
        // only package.json's version, so every deploy busts the cache --
        // not only a version bump -- because a deploy that changes a
        // response shape (e.g. phase 3 adding `payments` to a work order)
        // must never hydrate an older, incompatible cache.
        buster: __APP_VERSION__,
        dehydrateOptions: {
          // See `shouldPersistQuery` above. The default keeps only status
          // "success", and the whole snapshot is rewritten on every cache
          // change, so a single failed refetch offline (or on a connection
          // that reports online but drops requests) erased the cached
          // session and inventory from IndexedDB while the open page kept
          // working -- the next reload then found nothing to show.
          shouldDehydrateQuery: shouldPersistQuery,
          // The IndexedDB outbox is the only durable transport for stock
          // movements. A paused mutation restored from this cache has no
          // mutationFn to resume with (no `setMutationDefaults`), so
          // persisting one would only bring back a zombie that fails on
          // reconnect and drops whatever the user did.
          shouldDehydrateMutation: () => false,
        },
      }}
    >
      {children}
    </PersistQueryClientProvider>
  );
}

import { useState, type ReactNode } from "react";
import { QueryClient } from "@tanstack/react-query";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";

import { idbPersister } from "../shared/offline/idbPersister";
import { shouldPersistQuery } from "./shouldPersistQuery";

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

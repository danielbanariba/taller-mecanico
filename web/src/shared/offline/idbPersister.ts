import { createStore, del, get, set, type UseStore } from "idb-keyval";
import type { PersistedClient, Persister } from "@tanstack/react-query-persist-client";

const PERSIST_KEY = "taller-query-cache";
const DEFAULT_STORE = createStore("taller-query-cache", "cache");

/**
 * An async `Persister` for `PersistQueryClientProvider` backed by
 * IndexedDB via idb-keyval, so the inventory list, item details,
 * histories and the session stay readable after closing and reopening the
 * app offline. A custom `store` makes this testable in isolation (see
 * `idbPersister.test.ts`); production code uses the default export below.
 */
export function createIdbPersister(store: UseStore = DEFAULT_STORE): Persister {
  return {
    async persistClient(persistedClient: PersistedClient) {
      await set(PERSIST_KEY, persistedClient, store);
    },
    async restoreClient() {
      return get<PersistedClient>(PERSIST_KEY, store);
    },
    async removeClient() {
      await del(PERSIST_KEY, store);
    },
  };
}

/** The real, browser-wide persister the app mounts in `AppProviders`. */
export const idbPersister: Persister = createIdbPersister(DEFAULT_STORE);

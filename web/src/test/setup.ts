import "@testing-library/jest-dom/vitest";
// jsdom has no IndexedDB implementation; every module that touches
// IndexedDB (the outbox, the persisted query cache) needs this polyfill in
// every test file, so it is loaded once here instead of per-file.
import "fake-indexeddb/auto";
import { onlineManager } from "@tanstack/react-query";
import { clear, createStore } from "idb-keyval";
import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "./server";

beforeAll(() => server.listen({ onUnhandledFrame: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// TanStack Query's `onlineManager` is a module-level singleton: a test that
// dispatches the browser's `offline` event (or calls `setOnline(false)`)
// would otherwise leave every later test in the same file paused offline.
afterEach(() => onlineManager.setOnline(true));

// `defaultOutbox` (outbox.ts) and `idbPersister` (idbPersister.ts) are
// module-level singletons shared by every test in a file, backed by the
// same named IndexedDB stores production code uses. Without this, a
// movement left queued by one test (e.g. one that mocks the PUT to always
// fail) would still be there for the next test to pick up and resend,
// exactly the kind of cross-test leakage `server.resetHandlers()` already
// prevents for MSW. `createStore` with the same names reconnects to the
// same underlying store, so this clears them without importing the
// production modules themselves.
const defaultOutboxStore = createStore("taller-outbox", "movements");
const defaultQueryCacheStore = createStore("taller-query-cache", "cache");

afterEach(async () => {
  await clear(defaultOutboxStore);
  await clear(defaultQueryCacheStore);
});

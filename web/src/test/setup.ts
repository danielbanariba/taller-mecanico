import "@testing-library/jest-dom/vitest";
// jsdom has no IndexedDB implementation; every module that touches
// IndexedDB (the outbox, the persisted query cache) needs this polyfill in
// every test file, so it is loaded once here instead of per-file.
import "fake-indexeddb/auto";
import { onlineManager } from "@tanstack/react-query";
import { clear, createStore } from "idb-keyval";
import { afterAll, afterEach, beforeAll, beforeEach } from "vitest";

import { server } from "./server";

beforeAll(() => server.listen({ onUnhandledFrame: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// `onUnhandledFrame: "error"` covers both HTTP requests and WebSocket
// connections (MSW 3's migration guide: it replaces 2.x's
// `onUnhandledRequest`). Its "error" strategy only logs a console error and
// answers the request with a network error -- it does NOT fail the test
// itself. A component that silently falls back when a request errors (e.g.
// a query with no explicit `onError` handling) would otherwise pass with an
// endpoint nobody mocked, exactly the gap a reviewer flagged for
// `CustomerDetailPage`'s unconditional orders query (see P2.S8.T2 in
// `openspec/changes/workshop-core/tasks.md`). `request:unhandled` fires for
// every such request regardless of the configured strategy, so collecting
// it here and failing in `afterEach` makes an unmocked request fail the
// test that issued it, instead of a silent console error.
let unhandledRequests: string[] = [];

server.events.on("request:unhandled", ({ request }) => {
  unhandledRequests.push(`${request.method} ${request.url}`);
});

beforeEach(() => {
  unhandledRequests = [];
});

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

// Runs last (registration order), so every other cleanup above still runs
// before a test fails here.
afterEach(() => {
  if (unhandledRequests.length > 0) {
    const requests = unhandledRequests;
    unhandledRequests = [];
    throw new Error(`Unhandled MSW request(s) -- add a handler: ${requests.join(", ")}`);
  }
});

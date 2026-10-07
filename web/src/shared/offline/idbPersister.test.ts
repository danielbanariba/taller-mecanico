import { createStore } from "idb-keyval";
import { describe, expect, it } from "vitest";

import { createIdbPersister } from "./idbPersister";
import type { PersistedClient } from "@tanstack/react-query-persist-client";

function fakeClient(buster: string): PersistedClient {
  return {
    timestamp: Date.now(),
    buster,
    clientState: { queries: [], mutations: [] },
  };
}

describe("createIdbPersister", () => {
  it("survives a reload: a new persister instance over the same IndexedDB store restores what the previous one persisted", async () => {
    // Defect this catches: persisting only to an in-memory variable (or to
    // a storage API that resets per instance) would make the whole
    // offline-readable-cache feature a no-op after closing the app.
    const store = createStore("taller-persister-test-1", "cache");
    const persister = createIdbPersister(store);
    const client = fakeClient("v1");

    await persister.persistClient(client);

    const reloaded = createIdbPersister(store);
    const restored = await reloaded.restoreClient();

    expect(restored).toEqual(client);
  });

  it("removeClient() deletes the persisted data so a later restoreClient() finds nothing", async () => {
    // Defect this catches: a logout that fails to clear the persisted
    // cache would let the next person who opens the app on this phone see
    // the previous workshop's inventory.
    const store = createStore("taller-persister-test-2", "cache");
    const persister = createIdbPersister(store);
    await persister.persistClient(fakeClient("v1"));

    await persister.removeClient();

    expect(await persister.restoreClient()).toBeUndefined();
  });
});

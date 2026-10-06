import { createStore, del, entries, get, set, type UseStore } from "idb-keyval";

import type { MovementKind } from "./api";

/**
 * One queued stock movement, persisted to IndexedDB so it survives closing
 * the app. `seq` is assigned at `add()` time from the store itself (not an
 * in-memory counter), so FIFO order is correct even across a reload: a new
 * `createOutbox()` instance over the same store continues the same sequence.
 */
export interface OutboxEntry {
  id: string;
  workshopId: string;
  itemId: string;
  kind: MovementKind;
  quantity: number;
  note?: string;
  occurredAt: string;
  attempts: number;
  lastError?: string;
  seq: number;
}

export type NewOutboxEntry = Omit<OutboxEntry, "attempts" | "lastError" | "seq">;

export interface Outbox {
  /** Persists a new queued movement and returns it with its assigned `seq`. */
  add(entry: NewOutboxEntry): Promise<OutboxEntry>;
  /** Removes an entry once it has been sent or definitively rejected. */
  remove(id: string): Promise<void>;
  /** Records a failed send attempt without removing the entry. */
  recordFailure(id: string, code: string): Promise<void>;
  /** All queued entries, oldest first. */
  list(): Promise<OutboxEntry[]>;
  /** Queued entries for one workshop only, oldest first. */
  listForWorkshop(workshopId: string): Promise<OutboxEntry[]>;
}

const DEFAULT_STORE = createStore("taller-outbox", "movements");

/**
 * Creates an outbox over the given idb-keyval store (a real browser store by
 * default, or an isolated one per test -- see `outbox.test.ts`).
 */
export function createOutbox(store: UseStore = DEFAULT_STORE): Outbox {
  async function nextSeq(): Promise<number> {
    const all = await entries<string, OutboxEntry>(store);
    return all.reduce((max, [, value]) => Math.max(max, value.seq), 0) + 1;
  }

  async function list(): Promise<OutboxEntry[]> {
    const all = await entries<string, OutboxEntry>(store);
    return all.map(([, value]) => value).sort((a, b) => a.seq - b.seq);
  }

  return {
    async add(entry) {
      const seq = await nextSeq();
      const stored: OutboxEntry = { ...entry, attempts: 0, seq };
      await set(stored.id, stored, store);
      return stored;
    },

    async remove(id) {
      await del(id, store);
    },

    async recordFailure(id, code) {
      const current = await get<OutboxEntry>(id, store);
      if (!current) {
        return;
      }
      await set(id, { ...current, attempts: current.attempts + 1, lastError: code }, store);
    },

    list,

    async listForWorkshop(workshopId) {
      const all = await list();
      return all.filter((entry) => entry.workshopId === workshopId);
    },
  };
}

/** The real, browser-wide outbox every screen uses in production. */
export const defaultOutbox: Outbox = createOutbox(DEFAULT_STORE);

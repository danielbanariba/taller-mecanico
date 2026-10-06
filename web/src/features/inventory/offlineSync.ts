import { ApiError } from "../../shared/api/http";
import { inventoryApi, type ItemStockSummary, type MovementOut } from "./api";
import type { Outbox, OutboxEntry } from "./outbox";

export interface SentMovement {
  id: string;
  movement: MovementOut;
  item: ItemStockSummary;
}

export interface RejectedMovement {
  entry: OutboxEntry;
  error: ApiError;
}

export interface FlushResult {
  sent: SentMovement[];
  removedWithError: RejectedMovement[];
}

export interface FlushDeps {
  outbox: Outbox;
  workshopId: string;
  putMovement?: typeof inventoryApi.putMovement;
}

/**
 * A rejection the server will never change its mind about on retry (the
 * item no longer exists, this exact movement id already landed, the
 * payload is invalid). Everything else -- no network, a 5xx, or a stale
 * session (401, which the session flow resolves via a login redirect) --
 * is kept queued and retried later.
 */
function isDefinitiveRejection(error: ApiError): boolean {
  return error.status >= 400 && error.status < 500 && error.status !== 401;
}

/**
 * Notifies whoever is waiting for one specific movement's outcome,
 * regardless of which flush pass actually processed it (see
 * `recordMovement` in `commands.ts`: a pass triggered by a *different*,
 * concurrent `recordMovement` call can pick up and send this entry before
 * this entry's own triggered pass gets its turn at the flush lock).
 */
type Outcome = { kind: "sent"; movement: MovementOut; item: ItemStockSummary } | { kind: "rejected"; error: ApiError };

const outcomeWaiters = new Map<string, Array<(outcome: Outcome) => void>>();

function notifyOutcome(id: string, outcome: Outcome): void {
  const waiters = outcomeWaiters.get(id);
  if (!waiters) {
    return;
  }
  outcomeWaiters.delete(id);
  for (const resolve of waiters) {
    resolve(outcome);
  }
}

/**
 * Resolves once entry `id` is sent or definitively rejected by *any* flush
 * pass. Never resolves while the entry stays queued (offline/5xx/401), so
 * callers must race it against something else that can time out, such as
 * `flushOutboxOnce`'s own returned promise.
 */
export function waitForOutcome(id: string): Promise<Outcome> {
  return new Promise((resolve) => {
    const list = outcomeWaiters.get(id) ?? [];
    list.push(resolve);
    outcomeWaiters.set(id, list);
  });
}

const outboxChangeListeners = new Set<() => void>();

/** Lets `recordMovement` and flush passes tell the UI to re-read the pending count. */
export function notifyOutboxChange(): void {
  for (const listener of outboxChangeListeners) {
    listener();
  }
}

export function subscribeOutboxChange(listener: () => void): () => void {
  outboxChangeListeners.add(listener);
  return () => outboxChangeListeners.delete(listener);
}

/**
 * How long one PUT is allowed to hang before the flush pass gives up on it
 * and treats it as a network failure. Every flush is serialized behind one
 * lock (see `withFlushLock`): without a bound here, a single request that
 * never settles (a dead connection the browser hasn't noticed yet) would
 * hold that lock forever and block every other item's movements too, not
 * just this one's.
 */
const PUT_TIMEOUT_MS = 20_000;

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new ApiError(0, "network_error")), ms);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        clearTimeout(timer);
        reject(error);
      },
    );
  });
}

async function runFlushPass(deps: FlushDeps): Promise<FlushResult> {
  const { outbox, workshopId } = deps;
  const putMovement = deps.putMovement ?? inventoryApi.putMovement;
  const sent: SentMovement[] = [];
  const removedWithError: RejectedMovement[] = [];

  const pending = await outbox.listForWorkshop(workshopId);

  for (const entry of pending) {
    try {
      const result = await withTimeout(
        putMovement(entry.id, {
          item_id: entry.itemId,
          kind: entry.kind,
          quantity: entry.quantity,
          note: entry.note,
          occurred_at: entry.occurredAt,
        }),
        PUT_TIMEOUT_MS,
      );
      await outbox.remove(entry.id);
      notifyOutboxChange();
      sent.push({ id: entry.id, movement: result.movement, item: result.item });
      notifyOutcome(entry.id, { kind: "sent", movement: result.movement, item: result.item });
    } catch (error) {
      if (error instanceof ApiError && isDefinitiveRejection(error)) {
        await outbox.remove(entry.id);
        notifyOutboxChange();
        removedWithError.push({ entry, error });
        notifyOutcome(entry.id, { kind: "rejected", error });
        continue;
      }
      // Not reachable with something other than ApiError in practice (http
      // always throws ApiError), but keep the queue intact defensively.
      const code = error instanceof ApiError ? error.code : "unknown_error";
      await outbox.recordFailure(entry.id, code);
      notifyOutboxChange();
      // Stop here: entries behind this one may depend on it (e.g. two
      // "adjust" movements on the same item), and we are very likely still
      // offline, so trying them now would just fail too.
      break;
    }
  }

  return { sent, removedWithError };
}

const FLUSH_LOCK_NAME = "taller-outbox-flush";

/** In-tab fallback mutex for environments without the Web Locks API (e.g. the test runner). */
let inTabChain: Promise<void> = Promise.resolve();

async function withFlushLock<T>(run: () => Promise<T>): Promise<T> {
  const locks = typeof navigator !== "undefined" ? navigator.locks : undefined;
  if (locks?.request) {
    // No `ifAvailable`: this *queues* behind any other holder (same tab or
    // another tab), rather than skipping, so every triggered flush is
    // guaranteed to eventually run its own pass over the then-current
    // outbox contents.
    return locks.request(FLUSH_LOCK_NAME, () => run());
  }

  const previous = inTabChain;
  let release = () => {};
  inTabChain = new Promise<void>((resolve) => {
    release = resolve;
  });
  await previous;
  try {
    return await run();
  } finally {
    release();
  }
}

/**
 * Runs one flush pass over the given workshop's outbox, serialized against
 * every other call to `flushOutboxOnce` (same tab or another tab via Web
 * Locks): movements are always sent to the server one at a time, in the
 * order they were queued, never as independent parallel requests whose
 * responses could be reconciled out of order.
 */
export function flushOutboxOnce(deps: FlushDeps): Promise<FlushResult> {
  return withFlushLock(() => runFlushPass(deps));
}

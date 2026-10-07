import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient, type QueryKey } from "@tanstack/react-query";

import { ApiError } from "../../shared/api/http";
import { useSession, workshopQueryKey } from "../auth/hooks";
import {
  inventoryApi,
  type ItemOut,
  type ListItemsParams,
  type CreateItemPayload,
  type UpdateItemPayload,
} from "./api";
import { applyMovementToItem, applyPendingOutboxEntries, recordMovement, type RecordMovementInput } from "./commands";
import { getInventoryErrorMessage } from "./copy";
import { flushOutboxOnce, subscribeOutboxChange, withFlushLock } from "./offlineSync";
import { defaultOutbox, type Outbox } from "./outbox";

/**
 * Every inventory key starts with the workshop it belongs to (see
 * `workshopQueryKey`): a list or item cached for one workshop is never
 * served to another workshop's session, and logging in as another workshop
 * drops it. `workshopId` is undefined only before the session resolves,
 * when every inventory query is disabled.
 */
const inventoryQueryKey = (workshopId: string | undefined) => [...workshopQueryKey(workshopId), "inventory"] as const;
const itemsQueryBase = (workshopId: string | undefined) => [...inventoryQueryKey(workshopId), "items"] as const;

export const itemsQueryKey = (workshopId: string | undefined, params: ListItemsParams = {}) =>
  [...itemsQueryBase(workshopId), params] as const;
export const itemQueryKey = (workshopId: string | undefined, id: string) =>
  [...inventoryQueryKey(workshopId), "item", id] as const;
export const movementsQueryKey = (workshopId: string | undefined, id: string) =>
  [...itemQueryKey(workshopId, id), "movements"] as const;

/** Debounces `value`, settling `delayMs` after the last change. */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

/** The current session's workshop id, or undefined before it resolves. */
function useWorkshopId(): string | undefined {
  const session = useSession();
  return session.data?.workshop.id;
}

interface FetchItemsFoldedDeps {
  outbox?: Outbox;
  listItems?: typeof inventoryApi.listItems;
}

/**
 * Fetches the item list and folds any still-queued outbox entries onto it,
 * with the fetch and the outbox read serialized against every flush pass
 * through `withFlushLock` (see `offlineSync.ts`): this is what keeps a
 * refetch (e.g. TanStack Query's refetch-on-window-focus) from landing in
 * the narrow window between a flush pass's PUT succeeding and it removing
 * the entry, which would otherwise fold that movement a second time onto
 * server data that already includes it. Dependencies are injectable so
 * tests can control the fetch and the outbox without touching the network
 * or IndexedDB.
 */
export function fetchItemsFolded(
  params: ListItemsParams,
  workshopId: string | undefined,
  deps: FetchItemsFoldedDeps = {},
): Promise<ItemOut[]> {
  const outbox = deps.outbox ?? defaultOutbox;
  const listItems = deps.listItems ?? inventoryApi.listItems;
  return withFlushLock(async () => {
    const items = await listItems(params);
    if (!workshopId) {
      return items;
    }
    const pending = await outbox.listForWorkshop(workshopId);
    if (pending.length === 0) {
      return items;
    }
    return items.map((item) => applyPendingOutboxEntries(item, pending));
  });
}

interface FetchItemFoldedDeps {
  outbox?: Outbox;
  getItem?: typeof inventoryApi.getItem;
}

/** Single-item equivalent of `fetchItemsFolded`; see its docstring. */
export function fetchItemFolded(
  id: string,
  workshopId: string | undefined,
  deps: FetchItemFoldedDeps = {},
): Promise<ItemOut> {
  const outbox = deps.outbox ?? defaultOutbox;
  const getItem = deps.getItem ?? inventoryApi.getItem;
  return withFlushLock(async () => {
    const item = await getItem(id);
    if (!workshopId) {
      return item;
    }
    const pending = await outbox.listForWorkshop(workshopId);
    if (pending.length === 0) {
      return item;
    }
    return applyPendingOutboxEntries(item, pending);
  });
}

export function useItems(params: ListItemsParams = {}) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: itemsQueryKey(workshopId, params),
    queryFn: () => fetchItemsFolded(params, workshopId),
    enabled: workshopId !== undefined,
  });
}

export function useItem(id: string) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: itemQueryKey(workshopId, id),
    queryFn: () => fetchItemFolded(id, workshopId),
    enabled: workshopId !== undefined,
  });
}

export function useMovements(id: string) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: movementsQueryKey(workshopId, id),
    queryFn: () => inventoryApi.listMovements(id),
    enabled: workshopId !== undefined,
  });
}

export function useCreateItem() {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: CreateItemPayload) => inventoryApi.createItem(payload),
    onSuccess: (item) => {
      queryClient.setQueryData(itemQueryKey(workshopId, item.id), item);
      queryClient.invalidateQueries({ queryKey: itemsQueryBase(workshopId) });
    },
  });
}

export function useUpdateItem(id: string) {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: UpdateItemPayload) => inventoryApi.updateItem(id, payload),
    onSuccess: (item) => {
      queryClient.setQueryData(itemQueryKey(workshopId, id), item);
      queryClient.invalidateQueries({ queryKey: itemsQueryBase(workshopId) });
    },
  });
}

export function useArchiveItem() {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (id: string) => inventoryApi.archiveItem(id),
    onSuccess: (_result, id) => {
      queryClient.removeQueries({ queryKey: itemQueryKey(workshopId, id) });
      queryClient.invalidateQueries({ queryKey: itemsQueryBase(workshopId) });
    },
  });
}

interface RecordMovementSnapshot {
  previousItem: ItemOut | undefined;
  previousLists: [QueryKey, ItemOut[] | undefined][];
}

/**
 * The one hook every screen uses to change stock (list stepper, detail
 * stepper and the physical count dialog). It applies the new stock to both
 * the list and detail caches before the request settles, reconciles with
 * the server's `item` summary once the movement is actually sent, and
 * rolls every cache back if it is definitively rejected.
 *
 * `recordMovement` resolves with `{status: "queued"}` while offline --
 * `onSuccess` below treats that as a no-op and keeps the optimistic state
 * from `onMutate` untouched, exactly as if the request were still in
 * flight. There is nothing to roll back in that case because nothing was
 * rejected; `useOfflineSync`'s flush is what eventually reconciles it.
 *
 * `networkMode: "always"` is load-bearing: the mutationFn only writes to
 * the IndexedDB outbox and never needs the network itself. Under the
 * default `"online"` mode, TanStack Query pauses a mutation while its
 * `onlineManager` reports offline, so the mutationFn never ran and the tap
 * never reached the outbox -- it only existed as a paused mutation, which
 * a reload discards (there are no mutation defaults to resume it with).
 */
export function useRecordMovement() {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();

  return useMutation({
    networkMode: "always",
    mutationFn: (input: RecordMovementInput) => {
      if (!workshopId) {
        // Every screen that calls this hook renders behind RequireSession,
        // which only renders its children once a workshop session exists.
        return Promise.reject(new ApiError(401, "not_authenticated"));
      }
      return recordMovement(input, { workshopId });
    },
    onMutate: async (input): Promise<RecordMovementSnapshot> => {
      await queryClient.cancelQueries({ queryKey: itemQueryKey(workshopId, input.itemId) });
      await queryClient.cancelQueries({ queryKey: itemsQueryBase(workshopId) });

      const previousItem = queryClient.getQueryData<ItemOut>(itemQueryKey(workshopId, input.itemId));
      const previousLists = queryClient.getQueriesData<ItemOut[]>({ queryKey: itemsQueryBase(workshopId) });

      queryClient.setQueryData<ItemOut>(itemQueryKey(workshopId, input.itemId), (current) =>
        current ? applyMovementToItem(current, input) : current,
      );
      queryClient.setQueriesData<ItemOut[]>({ queryKey: itemsQueryBase(workshopId) }, (current) =>
        current?.map((item) => (item.id === input.itemId ? applyMovementToItem(item, input) : item)),
      );

      return { previousItem, previousLists };
    },
    onError: (_error, input, onMutateResult) => {
      if (!onMutateResult) {
        return;
      }
      queryClient.setQueryData(itemQueryKey(workshopId, input.itemId), onMutateResult.previousItem);
      for (const [key, data] of onMutateResult.previousLists) {
        queryClient.setQueryData(key, data);
      }
      // A rejection this mutation actually threw is definitive (recordMovement
      // never throws for a network/offline failure, only for a 4xx the
      // server will never reconsider). Refetch the authoritative state
      // instead of trusting the rolled-back snapshot alone, in case another
      // movement (a background flush, another device) has since changed it.
      queryClient.invalidateQueries({ queryKey: itemQueryKey(workshopId, input.itemId) });
      queryClient.invalidateQueries({ queryKey: itemsQueryBase(workshopId) });
    },
    onSuccess: (result, input) => {
      if (result.status === "queued") {
        return;
      }
      queryClient.setQueryData<ItemOut>(itemQueryKey(workshopId, input.itemId), (current) =>
        current ? { ...current, ...result.item } : current,
      );
      queryClient.setQueriesData<ItemOut[]>({ queryKey: itemsQueryBase(workshopId) }, (current) =>
        current?.map((item) => (item.id === input.itemId ? { ...item, ...result.item } : item)),
      );
      queryClient.invalidateQueries({ queryKey: movementsQueryKey(workshopId, input.itemId) });
    },
  });
}

const FLUSH_INTERVAL_MS = 30_000;

export interface OfflineSyncStatus {
  pendingCount: number;
  syncing: boolean;
  lastErrorMessage: string | undefined;
}

const INITIAL_SYNC_STATUS: OfflineSyncStatus = { pendingCount: 0, syncing: false, lastErrorMessage: undefined };

function syncStatusQueryKey(workshopId: string | undefined) {
  return [...inventoryQueryKey(workshopId), "sync-status"] as const;
}

/**
 * Drives the outbox flush for `workshopId`: once on mount (app start),
 * whenever the browser's `online` event fires, every 30s while the tab is
 * open, and whenever the outbox changes (so the pending count reacts to a
 * `recordMovement` call immediately, not just on the next scheduled
 * flush). Call once near the root of the authenticated area (see
 * `RequireSession`); every screen just reads the banner it renders.
 *
 * `flushOutboxOnce` is called directly here (not through `useQuery`'s own
 * fetch/refetch pipeline): TanStack Query dedupes concurrent fetches for
 * the same query, which would merge an `online`-triggered flush into one
 * already in flight instead of giving it its own fresh pass over the
 * outbox -- exactly the out-of-order risk `flushOutboxOnce`'s own queueing
 * (see `offlineSync.ts`) exists to prevent. The status this hook reports
 * is still kept in the query cache via `setQueryData`, not a local
 * `useState`, purely so a mount-time flush has somewhere sanctioned to
 * publish its result from inside an effect (an external store, same as
 * the cache every other screen already reads through `useQuery`) --
 * `recordMovement` itself remains the one true transport.
 */
export function useOfflineSync(workshopId: string | undefined): OfflineSyncStatus {
  const queryClient = useQueryClient();

  const statusQuery = useQuery({
    queryKey: syncStatusQueryKey(workshopId),
    queryFn: () => INITIAL_SYNC_STATUS,
    enabled: false,
    initialData: INITIAL_SYNC_STATUS,
  });

  useEffect(() => {
    if (workshopId === undefined) {
      // No session yet: nothing to flush or count. `OfflineStatusBanner`
      // only mounts this hook once a session exists, so this is only a
      // defensive guard, not a transition this effect needs to react to.
      return;
    }
    const key = syncStatusQueryKey(workshopId);
    const patch = (change: Partial<OfflineSyncStatus>) =>
      queryClient.setQueryData<OfflineSyncStatus>(key, (current) => ({ ...(current ?? INITIAL_SYNC_STATUS), ...change }));

    const refreshPendingCount = async () => {
      const entries = await defaultOutbox.listForWorkshop(workshopId);
      patch({ pendingCount: entries.length });
    };

    const runFlush = async () => {
      patch({ syncing: true });
      try {
        const result = await flushOutboxOnce({ outbox: defaultOutbox, workshopId });
        if (result.removedWithError.length > 0) {
          const last = result.removedWithError[result.removedWithError.length - 1];
          patch({ lastErrorMessage: last ? getInventoryErrorMessage(last.error.code) : undefined });
        }
        if (result.sent.length > 0 || result.removedWithError.length > 0) {
          queryClient.invalidateQueries({ queryKey: inventoryQueryKey(workshopId) });
        }
      } finally {
        patch({ syncing: false });
        await refreshPendingCount();
      }
    };

    void refreshPendingCount();
    void runFlush();

    const unsubscribe = subscribeOutboxChange(() => void refreshPendingCount());
    const handleOnline = () => void runFlush();
    window.addEventListener("online", handleOnline);
    const interval = window.setInterval(() => void runFlush(), FLUSH_INTERVAL_MS);

    return () => {
      unsubscribe();
      window.removeEventListener("online", handleOnline);
      window.clearInterval(interval);
    };
  }, [workshopId, queryClient]);

  return statusQuery.data ?? INITIAL_SYNC_STATUS;
}

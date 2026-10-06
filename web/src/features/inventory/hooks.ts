import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient, type QueryKey } from "@tanstack/react-query";

import {
  inventoryApi,
  type ItemOut,
  type ListItemsParams,
  type CreateItemPayload,
  type UpdateItemPayload,
} from "./api";
import { applyMovementToItem, recordMovement, type RecordMovementInput } from "./commands";

const ITEMS_QUERY_BASE = ["inventory", "items"] as const;

export const itemsQueryKey = (params: ListItemsParams = {}) => [...ITEMS_QUERY_BASE, params] as const;
export const itemQueryKey = (id: string) => ["inventory", "item", id] as const;
export const movementsQueryKey = (id: string) => ["inventory", "item", id, "movements"] as const;

/** Debounces `value`, settling `delayMs` after the last change. */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

export function useItems(params: ListItemsParams = {}) {
  return useQuery({
    queryKey: itemsQueryKey(params),
    queryFn: () => inventoryApi.listItems(params),
  });
}

export function useItem(id: string) {
  return useQuery({
    queryKey: itemQueryKey(id),
    queryFn: () => inventoryApi.getItem(id),
  });
}

export function useMovements(id: string) {
  return useQuery({
    queryKey: movementsQueryKey(id),
    queryFn: () => inventoryApi.listMovements(id),
  });
}

export function useCreateItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateItemPayload) => inventoryApi.createItem(payload),
    onSuccess: (item) => {
      queryClient.setQueryData(itemQueryKey(item.id), item);
      queryClient.invalidateQueries({ queryKey: ITEMS_QUERY_BASE });
    },
  });
}

export function useUpdateItem(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateItemPayload) => inventoryApi.updateItem(id, payload),
    onSuccess: (item) => {
      queryClient.setQueryData(itemQueryKey(id), item);
      queryClient.invalidateQueries({ queryKey: ITEMS_QUERY_BASE });
    },
  });
}

export function useArchiveItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => inventoryApi.archiveItem(id),
    onSuccess: (_result, id) => {
      queryClient.removeQueries({ queryKey: itemQueryKey(id) });
      queryClient.invalidateQueries({ queryKey: ITEMS_QUERY_BASE });
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
 * the server's `item` summary on success, and rolls every cache back on
 * failure.
 */
export function useRecordMovement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: RecordMovementInput) => recordMovement(input),
    onMutate: async (input): Promise<RecordMovementSnapshot> => {
      await queryClient.cancelQueries({ queryKey: itemQueryKey(input.itemId) });
      await queryClient.cancelQueries({ queryKey: ITEMS_QUERY_BASE });

      const previousItem = queryClient.getQueryData<ItemOut>(itemQueryKey(input.itemId));
      const previousLists = queryClient.getQueriesData<ItemOut[]>({ queryKey: ITEMS_QUERY_BASE });

      queryClient.setQueryData<ItemOut>(itemQueryKey(input.itemId), (current) =>
        current ? applyMovementToItem(current, input) : current,
      );
      queryClient.setQueriesData<ItemOut[]>({ queryKey: ITEMS_QUERY_BASE }, (current) =>
        current?.map((item) => (item.id === input.itemId ? applyMovementToItem(item, input) : item)),
      );

      return { previousItem, previousLists };
    },
    onError: (_error, input, onMutateResult) => {
      if (!onMutateResult) {
        return;
      }
      queryClient.setQueryData(itemQueryKey(input.itemId), onMutateResult.previousItem);
      for (const [key, data] of onMutateResult.previousLists) {
        queryClient.setQueryData(key, data);
      }
    },
    onSuccess: (result, input) => {
      queryClient.setQueryData<ItemOut>(itemQueryKey(input.itemId), (current) =>
        current ? { ...current, ...result.item } : current,
      );
      queryClient.setQueriesData<ItemOut[]>({ queryKey: ITEMS_QUERY_BASE }, (current) =>
        current?.map((item) => (item.id === input.itemId ? { ...item, ...result.item } : item)),
      );
      queryClient.invalidateQueries({ queryKey: movementsQueryKey(input.itemId) });
    },
  });
}

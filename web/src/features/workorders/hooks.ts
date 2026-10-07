import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useWorkshopId, workshopQueryKey } from "../auth/hooks";
import { inventoryQueryKey } from "../inventory/hooks";
import {
  workOrdersApi,
  type ChangeStatusPayload,
  type CreateLinePayload,
  type CreateWorkOrderPayload,
  type StatusGroup,
  type UpdateLinePayload,
  type WorkOrderOut,
  type WorkOrderSummaryOut,
} from "./api";

const workOrdersQueryBase = (workshopId: string | undefined) =>
  [...workshopQueryKey(workshopId), "workOrders"] as const;

export const workOrdersListQueryKey = (
  workshopId: string | undefined,
  params: { statusGroup: StatusGroup; limit: number; vehicleId?: string; customerId?: string },
) => [...workOrdersQueryBase(workshopId), "list", params] as const;

export const workOrderQueryKey = (workshopId: string | undefined, id: string) =>
  [...workOrdersQueryBase(workshopId), "detail", id] as const;

/** Matches the API's own default (`design.md`'s "API surface per phase"). */
const DEFAULT_LIMIT = 50;

/**
 * One status group's work orders, paginated with the API's keyset
 * (`before_number`, per `design.md`): a full page means there may be
 * more, so `getNextPageParam` asks for the oldest number on this page.
 * Historial calls `fetchNextPage` as the mechanic scrolls; Abiertas in
 * practice never fills a page, but sharing one hook keeps both tabs'
 * query key shape and cache invalidation identical.
 */
export function useWorkOrders(statusGroup: StatusGroup, limit: number = DEFAULT_LIMIT) {
  const workshopId = useWorkshopId();
  const params = { statusGroup, limit };

  return useInfiniteQuery({
    queryKey: workOrdersListQueryKey(workshopId, params),
    queryFn: ({ pageParam }: { pageParam: number | undefined }) =>
      workOrdersApi.listWorkOrders({ statusGroup, limit, beforeNumber: pageParam }),
    initialPageParam: undefined as number | undefined,
    getNextPageParam: (lastPage: WorkOrderSummaryOut[]): number | undefined =>
      lastPage.length < limit ? undefined : lastPage[lastPage.length - 1]?.number,
    enabled: workshopId !== undefined,
  });
}

export function useWorkOrder(id: string) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: workOrderQueryKey(workshopId, id),
    queryFn: () => workOrdersApi.getWorkOrder(id),
    enabled: workshopId !== undefined,
  });
}

/**
 * One vehicle's service history for its detail screen, newest number first
 * (the API's own order, across every status). Not paginated: `DEFAULT_LIMIT`
 * already covers far more orders than one vehicle realistically accumulates.
 * The query key shares `workOrdersQueryBase`'s "list" prefix, so it is
 * already covered by every existing order/line/status mutation's
 * invalidation above -- no extra wiring needed.
 */
export function useWorkOrdersForVehicle(vehicleId: string) {
  const workshopId = useWorkshopId();
  const params = { statusGroup: "all" as StatusGroup, limit: DEFAULT_LIMIT, vehicleId };
  return useQuery({
    queryKey: workOrdersListQueryKey(workshopId, params),
    queryFn: () => workOrdersApi.listWorkOrders({ statusGroup: "all", limit: DEFAULT_LIMIT, vehicleId }),
    enabled: workshopId !== undefined && vehicleId !== "",
  });
}

/** Same as {@link useWorkOrdersForVehicle}, scoped to a customer across every one of their vehicles, for the customer detail screen. */
export function useWorkOrdersForCustomer(customerId: string) {
  const workshopId = useWorkshopId();
  const params = { statusGroup: "all" as StatusGroup, limit: DEFAULT_LIMIT, customerId };
  return useQuery({
    queryKey: workOrdersListQueryKey(workshopId, params),
    queryFn: () => workOrdersApi.listWorkOrders({ statusGroup: "all", limit: DEFAULT_LIMIT, customerId }),
    enabled: workshopId !== undefined && customerId !== "",
  });
}

export function useCreateWorkOrder() {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: CreateWorkOrderPayload) => workOrdersApi.createWorkOrder(payload),
    onSuccess: (order) => {
      queryClient.setQueryData(workOrderQueryKey(workshopId, order.id), order);
      queryClient.invalidateQueries({ queryKey: workOrdersQueryBase(workshopId) });
    },
  });
}

/**
 * Every line mutation (add, edit, remove) returns the whole order
 * (`design.md`'s "API surface per phase" note), so the detail query is
 * updated from that one round trip instead of a refetch, and every list
 * is invalidated since an edited line can change a summary's total.
 */
function useLineMutationCacheUpdate(orderId: string) {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return (order: WorkOrderOut) => {
    queryClient.setQueryData(workOrderQueryKey(workshopId, orderId), order);
    queryClient.invalidateQueries({ queryKey: workOrdersQueryBase(workshopId) });
  };
}

export function useAddLine(orderId: string) {
  const onSuccess = useLineMutationCacheUpdate(orderId);
  return useMutation({
    mutationFn: (payload: CreateLinePayload) => workOrdersApi.addLine(orderId, payload),
    onSuccess,
  });
}

export function useUpdateLine(orderId: string) {
  const onSuccess = useLineMutationCacheUpdate(orderId);
  return useMutation({
    mutationFn: ({ lineId, payload }: { lineId: string; payload: UpdateLinePayload }) =>
      workOrdersApi.updateLine(orderId, lineId, payload),
    onSuccess,
  });
}

export function useRemoveLine(orderId: string) {
  const onSuccess = useLineMutationCacheUpdate(orderId);
  return useMutation({
    mutationFn: (lineId: string) => workOrdersApi.removeLine(orderId, lineId),
    onSuccess,
  });
}

/**
 * A status change also moves stock for a consuming transition
 * (`design.md`'s AD-7/AD-4), so beyond the usual order/list cache update
 * every other line mutation does, this also invalidates
 * `inventoryQueryKey` -- otherwise the inventory list/detail screens
 * would keep showing the pre-consumption stock until an unrelated
 * refetch happened to run.
 */
export function useChangeStatus(orderId: string) {
  const onOrderSuccess = useLineMutationCacheUpdate(orderId);
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: ChangeStatusPayload) => workOrdersApi.changeStatus(orderId, payload),
    onSuccess: (order) => {
      onOrderSuccess(order);
      queryClient.invalidateQueries({ queryKey: inventoryQueryKey(workshopId) });
    },
  });
}

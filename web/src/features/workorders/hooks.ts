import { useInfiniteQuery, useQuery } from "@tanstack/react-query";

import { useWorkshopId, workshopQueryKey } from "../auth/hooks";
import { workOrdersApi, type StatusGroup, type WorkOrderSummaryOut } from "./api";

const workOrdersQueryBase = (workshopId: string | undefined) =>
  [...workshopQueryKey(workshopId), "workOrders"] as const;

export const workOrdersListQueryKey = (
  workshopId: string | undefined,
  params: { statusGroup: StatusGroup; limit: number },
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

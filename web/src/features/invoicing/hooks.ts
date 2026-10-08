import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useWorkshopId, workshopQueryKey } from "../auth/hooks";
import {
  invoicingApi,
  type CreateCaiRangePayload,
  type FiscalProfileSavePayload,
  type UpdateCaiRangePayload,
} from "./api";

/**
 * `GET /invoicing/settings`'s query key (`design.md`'s AD-15 "Query keys"
 * table): persisted, so a previously fetched settings screen -- and the
 * order detail's own readiness check -- still render offline.
 */
export const invoicingSettingsQueryKey = (workshopId: string | undefined) =>
  [...workshopQueryKey(workshopId), "invoicing", "settings"] as const;

export function useInvoicingSettings() {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: invoicingSettingsQueryKey(workshopId),
    queryFn: () => invoicingApi.getSettings(),
    enabled: workshopId !== undefined,
  });
}

/**
 * Saving the profile can change readiness (a code change can lock/unlock
 * ranges) and the issuance gate, so it invalidates the one settings query
 * every other invoicing screen reads from (AD-3/AD-15).
 */
export function useSaveFiscalProfile() {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: FiscalProfileSavePayload) => invoicingApi.saveProfile(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoicingSettingsQueryKey(workshopId) });
    },
  });
}

export function useCreateCaiRange() {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: CreateCaiRangePayload) => invoicingApi.createCaiRange(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoicingSettingsQueryKey(workshopId) });
    },
  });
}

export function useUpdateCaiRange(id: string) {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: UpdateCaiRangePayload) => invoicingApi.updateCaiRange(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoicingSettingsQueryKey(workshopId) });
    },
  });
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useWorkshopId, workshopQueryKey } from "../auth/hooks";
import { workOrderQueryKey } from "../workorders/hooks";
import {
  invoicingApi,
  type CreateCaiRangePayload,
  type FiscalProfileSavePayload,
  type IssueInvoicePayload,
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
export function useSaveProfile() {
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

/** One issued Factura's own query key (AD-15's "Query keys" table): persisted, so a previously fetched Factura still renders offline for its detail and print routes. */
export const invoiceQueryKey = (workshopId: string | undefined, id: string) =>
  [...workshopQueryKey(workshopId), "invoicing", "invoices", "detail", id] as const;

/** An order's own list of issued Factura summaries (AD-15's "Query keys" table). */
export const orderInvoicesQueryKey = (workshopId: string | undefined, orderId: string) =>
  [...workshopQueryKey(workshopId), "invoicing", "invoices", "byOrder", orderId] as const;

export function useInvoice(id: string) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: invoiceQueryKey(workshopId, id),
    queryFn: () => invoicingApi.getInvoice(id),
    enabled: workshopId !== undefined && id !== "",
  });
}

export function useOrderInvoices(orderId: string) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: orderInvoicesQueryKey(workshopId, orderId),
    queryFn: () => invoicingApi.listOrderInvoices(orderId),
    enabled: workshopId !== undefined && orderId !== "",
  });
}

/**
 * Issuing a Factura changes the order's own `active_invoice`/`lines_editable`
 * (the `work-orders` spec's invoicing lock), this order's invoice list, and
 * readiness (a range can move to `exhausted`) -- so it invalidates all three
 * alongside caching the new invoice itself (AD-15's "Query keys" table).
 */
export function useIssueInvoice(orderId: string) {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: IssueInvoicePayload) => invoicingApi.issueInvoice(payload),
    onSuccess: (invoice) => {
      queryClient.setQueryData(invoiceQueryKey(workshopId, invoice.id), invoice);
      queryClient.invalidateQueries({ queryKey: workOrderQueryKey(workshopId, orderId) });
      queryClient.invalidateQueries({ queryKey: orderInvoicesQueryKey(workshopId, orderId) });
      queryClient.invalidateQueries({ queryKey: invoicingSettingsQueryKey(workshopId) });
    },
  });
}

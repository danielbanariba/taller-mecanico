import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useWorkshopId, workshopQueryKey } from "../auth/hooks";
import { workOrderQueryKey } from "../workorders/hooks";
import {
  invoicingApi,
  type CreateCaiRangePayload,
  type FiscalProfileSavePayload,
  type IssueCreditNotePayload,
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

/**
 * `enabled` lets a caller gate the fetch on something besides the id
 * itself -- `InvoiceSection` only knows an order's documents once a
 * fiscal profile exists, and must not fire this request for every
 * workshop that never opted in.
 */
export function useOrderInvoices(orderId: string, enabled = true) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: orderInvoicesQueryKey(workshopId, orderId),
    queryFn: () => invoicingApi.listOrderInvoices(orderId),
    enabled: enabled && workshopId !== undefined && orderId !== "",
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

/** A credit note's own query key (AD-15's "Query keys" table): persisted, so a previously fetched credit note still renders offline for its detail route. */
export const creditNoteQueryKey = (workshopId: string | undefined, id: string) =>
  [...workshopQueryKey(workshopId), "invoicing", "creditNotes", "detail", id] as const;

export function useCreditNote(id: string) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: creditNoteQueryKey(workshopId, id),
    queryFn: () => invoicingApi.getCreditNote(id),
    enabled: workshopId !== undefined && id !== "",
  });
}

/**
 * Crediting a Factura releases the invoiced-order lock (AD-13): the
 * order's own `active_invoice`/`lines_editable` change, the invoice
 * gains its `credit_note` reference, this order's document list gains
 * the new document, and readiness can change (the `06` range may move
 * to exhausted) -- so it invalidates all four alongside caching the
 * credit note itself (AD-15's "Query keys" table).
 */
export function useIssueCreditNote(orderId: string, invoiceId: string) {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: IssueCreditNotePayload) => invoicingApi.issueCreditNote(payload),
    onSuccess: (creditNote) => {
      queryClient.setQueryData(creditNoteQueryKey(workshopId, creditNote.id), creditNote);
      queryClient.invalidateQueries({ queryKey: invoiceQueryKey(workshopId, invoiceId) });
      queryClient.invalidateQueries({ queryKey: orderInvoicesQueryKey(workshopId, orderId) });
      queryClient.invalidateQueries({ queryKey: workOrderQueryKey(workshopId, orderId) });
      queryClient.invalidateQueries({ queryKey: invoicingSettingsQueryKey(workshopId) });
    },
  });
}

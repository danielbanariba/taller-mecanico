import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useWorkshopId, workshopQueryKey } from "../auth/hooks";
import {
  customersApi,
  type CreateCustomerPayload,
  type CreateVehiclePayload,
  type ListCustomersParams,
  type ListVehiclesParams,
  type UpdateCustomerPayload,
  type UpdateVehiclePayload,
} from "./api";

/**
 * Every customer key starts with the workshop it belongs to (see
 * `workshopQueryKey`'s own docstring), so a workshop switch's cache purge
 * (`startSession` in `features/auth/hooks.ts`) drops these the same way it
 * already drops inventory's.
 */
const customersQueryBase = (workshopId: string | undefined) =>
  [...workshopQueryKey(workshopId), "customers"] as const;
const customersListBase = (workshopId: string | undefined) => [...customersQueryBase(workshopId), "list"] as const;

export const customersListQueryKey = (workshopId: string | undefined, params: ListCustomersParams = {}) =>
  [...customersListBase(workshopId), params] as const;
export const customerQueryKey = (workshopId: string | undefined, id: string) =>
  [...customersQueryBase(workshopId), "detail", id] as const;

/** A customer's own vehicle list, nested under that customer's key (see the "Query keys" table in `design.md`). */
export const vehiclesForCustomerQueryKey = (workshopId: string | undefined, customerId: string) =>
  [...customersQueryBase(workshopId), "detail", customerId, "vehicles"] as const;

const vehiclesQueryBase = (workshopId: string | undefined) => [...workshopQueryKey(workshopId), "vehicles"] as const;
export const vehicleQueryKey = (workshopId: string | undefined, id: string) =>
  [...vehiclesQueryBase(workshopId), "detail", id] as const;

/** Debounces `value`, settling `delayMs` after the last change. */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

export function useCustomers(params: ListCustomersParams = {}) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: customersListQueryKey(workshopId, params),
    queryFn: () => customersApi.listCustomers(params),
    enabled: workshopId !== undefined,
  });
}

export function useCustomer(id: string) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: customerQueryKey(workshopId, id),
    queryFn: () => customersApi.getCustomer(id),
    enabled: workshopId !== undefined,
  });
}

export function useCreateCustomer() {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: CreateCustomerPayload) => customersApi.createCustomer(payload),
    onSuccess: (customer) => {
      queryClient.setQueryData(customerQueryKey(workshopId, customer.id), customer);
      queryClient.invalidateQueries({ queryKey: customersListBase(workshopId) });
    },
  });
}

export function useUpdateCustomer(id: string) {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: UpdateCustomerPayload) => customersApi.updateCustomer(id, payload),
    onSuccess: (customer) => {
      queryClient.setQueryData(customerQueryKey(workshopId, id), customer);
      queryClient.invalidateQueries({ queryKey: customersListBase(workshopId) });
    },
  });
}

export function useArchiveCustomer() {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (id: string) => customersApi.archiveCustomer(id),
    onSuccess: (_result, id) => {
      queryClient.removeQueries({ queryKey: customerQueryKey(workshopId, id) });
      queryClient.invalidateQueries({ queryKey: customersListBase(workshopId) });
      // Archiving a customer cascades to archive every one of its active
      // vehicles (AD-15), so this customer's vehicle list and every
      // individual vehicle detail cached under it go stale too.
      queryClient.invalidateQueries({ queryKey: vehiclesForCustomerQueryKey(workshopId, id) });
      queryClient.invalidateQueries({ queryKey: vehiclesQueryBase(workshopId) });
    },
  });
}

export function useVehiclesForCustomer(customerId: string, params: ListVehiclesParams = {}) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: vehiclesForCustomerQueryKey(workshopId, customerId),
    queryFn: () => customersApi.listVehiclesForCustomer(customerId, params),
    enabled: workshopId !== undefined && customerId !== "",
  });
}

/**
 * `id !== ""` matters beyond the usual guard: `NewWorkOrderPage` calls this
 * with a possibly-empty `?vehiculo=` query param, and without it this would
 * fire a request to `/api/vehicles/` (no id) on every visit to the plain
 * `/ordenes/nueva` flow.
 */
export function useVehicle(id: string) {
  const workshopId = useWorkshopId();
  return useQuery({
    queryKey: vehicleQueryKey(workshopId, id),
    queryFn: () => customersApi.getVehicle(id),
    enabled: workshopId !== undefined && id !== "",
  });
}

export function useCreateVehicle(customerId: string) {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: CreateVehiclePayload) => customersApi.createVehicle(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: vehiclesForCustomerQueryKey(workshopId, customerId) });
    },
  });
}

export function useUpdateVehicle(id: string, customerId: string) {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (payload: UpdateVehiclePayload) => customersApi.updateVehicle(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: vehicleQueryKey(workshopId, id) });
      queryClient.invalidateQueries({ queryKey: vehiclesForCustomerQueryKey(workshopId, customerId) });
    },
  });
}

export function useArchiveVehicle(customerId: string) {
  const queryClient = useQueryClient();
  const workshopId = useWorkshopId();
  return useMutation({
    mutationFn: (id: string) => customersApi.archiveVehicle(id),
    onSuccess: (_result, id) => {
      queryClient.removeQueries({ queryKey: vehicleQueryKey(workshopId, id) });
      queryClient.invalidateQueries({ queryKey: vehiclesForCustomerQueryKey(workshopId, customerId) });
    },
  });
}

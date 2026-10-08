import { http } from "../../shared/api/http";

export interface CustomerOut {
  id: string;
  full_name: string;
  phone: string | null;
  phone_is_mobile: boolean | null;
  notes: string | null;
  billing_name: string | null;
  rtn: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ListCustomersParams {
  q?: string;
  includeArchived?: boolean;
}

export interface CreateCustomerPayload {
  id: string;
  full_name: string;
  phone?: string;
  notes?: string;
  billing_name?: string;
  rtn?: string;
}

export interface UpdateCustomerPayload {
  full_name?: string;
  phone?: string | null;
  notes?: string | null;
  billing_name?: string | null;
  rtn?: string | null;
}

export type VehicleType = "car" | "motorcycle" | "other";

export interface VehicleOut {
  id: string;
  customer_id: string;
  vehicle_type: VehicleType;
  make: string;
  model: string | null;
  year: number | null;
  color: string | null;
  plate: string | null;
  notes: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

/** `GET /vehicles/{id}` only -- embeds the owner, unlike every other vehicle shape. */
export interface VehicleDetailOut extends VehicleOut {
  owner: CustomerOut;
}

export interface ListVehiclesParams {
  includeArchived?: boolean;
}

export interface CreateVehiclePayload {
  id: string;
  customer_id: string;
  vehicle_type: VehicleType;
  make: string;
  model?: string;
  year?: number;
  color?: string;
  plate?: string;
  notes?: string;
}

/** `customer_id` is intentionally absent: a vehicle's owner never changes after creation. */
export interface UpdateVehiclePayload {
  vehicle_type?: VehicleType;
  make?: string;
  model?: string | null;
  year?: number | null;
  color?: string | null;
  plate?: string | null;
  notes?: string | null;
}

function buildListQuery(params: ListCustomersParams): string {
  const query = new URLSearchParams();
  if (params.q) {
    query.set("q", params.q);
  }
  if (params.includeArchived) {
    query.set("include_archived", "true");
  }
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

function buildVehicleListQuery(params: ListVehiclesParams): string {
  return params.includeArchived ? "?include_archived=true" : "";
}

export const customersApi = {
  listCustomers: (params: ListCustomersParams = {}) =>
    http.get<CustomerOut[]>(`/api/customers${buildListQuery(params)}`),
  getCustomer: (id: string) => http.get<CustomerOut>(`/api/customers/${id}`),
  createCustomer: (payload: CreateCustomerPayload) => http.post<CustomerOut>("/api/customers", payload),
  updateCustomer: (id: string, payload: UpdateCustomerPayload) =>
    http.patch<CustomerOut>(`/api/customers/${id}`, payload),
  archiveCustomer: (id: string) => http.post<void>(`/api/customers/${id}/archive`),
  listVehiclesForCustomer: (customerId: string, params: ListVehiclesParams = {}) =>
    http.get<VehicleOut[]>(`/api/customers/${customerId}/vehicles${buildVehicleListQuery(params)}`),
  getVehicle: (id: string) => http.get<VehicleDetailOut>(`/api/vehicles/${id}`),
  createVehicle: (payload: CreateVehiclePayload) => http.post<VehicleOut>("/api/vehicles", payload),
  updateVehicle: (id: string, payload: UpdateVehiclePayload) =>
    http.patch<VehicleOut>(`/api/vehicles/${id}`, payload),
  archiveVehicle: (id: string) => http.post<void>(`/api/vehicles/${id}/archive`),
};

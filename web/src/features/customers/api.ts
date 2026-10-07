import { http } from "../../shared/api/http";

export interface CustomerOut {
  id: string;
  full_name: string;
  phone: string | null;
  phone_is_mobile: boolean | null;
  notes: string | null;
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
}

export interface UpdateCustomerPayload {
  full_name?: string;
  phone?: string | null;
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

export const customersApi = {
  listCustomers: (params: ListCustomersParams = {}) =>
    http.get<CustomerOut[]>(`/api/customers${buildListQuery(params)}`),
  getCustomer: (id: string) => http.get<CustomerOut>(`/api/customers/${id}`),
  createCustomer: (payload: CreateCustomerPayload) => http.post<CustomerOut>("/api/customers", payload),
  updateCustomer: (id: string, payload: UpdateCustomerPayload) =>
    http.patch<CustomerOut>(`/api/customers/${id}`, payload),
  archiveCustomer: (id: string) => http.post<void>(`/api/customers/${id}/archive`),
};

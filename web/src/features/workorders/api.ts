import { http } from "../../shared/api/http";

export type WorkOrderStatus = "quote" | "approved" | "in_progress" | "completed" | "delivered" | "cancelled";
export type LineKind = "labor" | "inventory_part" | "external_part";
export type StatusGroup = "open" | "closed" | "all";

export interface WorkOrderVehicleOut {
  id: string;
  vehicle_type: string;
  make: string;
  model: string | null;
  year: number | null;
  plate: string | null;
}

export interface WorkOrderCustomerOut {
  id: string;
  full_name: string;
}

/** `WorkOrderOut.customer` only -- adds the phone fields the summary shape has no use for. */
export interface WorkOrderCustomerDetailOut extends WorkOrderCustomerOut {
  phone: string | null;
  phone_is_mobile: boolean | null;
}

export interface WorkOrderLineOut {
  id: string;
  kind: LineKind;
  item_id: string | null;
  description: string;
  quantity: number;
  unit_price_cents: number;
  line_total_cents: number;
  stock_posted_quantity: number;
  created_at: string;
  updated_at: string;
}

export interface WorkOrderSummaryOut {
  id: string;
  number: number;
  status: WorkOrderStatus;
  vehicle: WorkOrderVehicleOut;
  customer: WorkOrderCustomerOut;
  total_cents: number;
  created_at: string;
  updated_at: string;
}

export interface WorkOrderOut {
  id: string;
  number: number;
  status: WorkOrderStatus;
  allowed_transitions: WorkOrderStatus[];
  lines_editable: boolean;
  vehicle: WorkOrderVehicleOut;
  customer: WorkOrderCustomerDetailOut;
  complaint: string | null;
  odometer_km: number | null;
  notes: string | null;
  lines: WorkOrderLineOut[];
  total_cents: number;
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  delivered_at: string | null;
  cancelled_at: string | null;
}

export interface ListWorkOrdersParams {
  statusGroup?: StatusGroup;
  vehicleId?: string;
  customerId?: string;
  beforeNumber?: number;
  limit?: number;
}

function buildListQuery(params: ListWorkOrdersParams): string {
  const query = new URLSearchParams();
  query.set("status_group", params.statusGroup ?? "open");
  if (params.vehicleId) {
    query.set("vehicle_id", params.vehicleId);
  }
  if (params.customerId) {
    query.set("customer_id", params.customerId);
  }
  if (params.beforeNumber !== undefined) {
    query.set("before_number", String(params.beforeNumber));
  }
  if (params.limit !== undefined) {
    query.set("limit", String(params.limit));
  }
  return `?${query.toString()}`;
}

export const workOrdersApi = {
  listWorkOrders: (params: ListWorkOrdersParams = {}) =>
    http.get<WorkOrderSummaryOut[]>(`/api/work-orders${buildListQuery(params)}`),
  getWorkOrder: (id: string) => http.get<WorkOrderOut>(`/api/work-orders/${id}`),
};

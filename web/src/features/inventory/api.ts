import { http } from "../../shared/api/http";

export type MovementKind = "in" | "out" | "adjust";

export interface ItemOut {
  id: string;
  name: string;
  category: string | null;
  unit: string;
  min_stock: number;
  sale_price_cents: number | null;
  notes: string | null;
  stock: number;
  needs_review: boolean;
  is_low: boolean;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MovementOut {
  id: string;
  item_id: string;
  kind: MovementKind;
  quantity: number;
  delta: number;
  note: string | null;
  occurred_at: string;
  recorded_at: string;
  created_by: string;
}

/** The subset of `ItemOut` the movement endpoint returns to reconcile stock. */
export type ItemStockSummary = Pick<ItemOut, "id" | "stock" | "needs_review" | "is_low">;

export interface MovementResult {
  movement: MovementOut;
  item: ItemStockSummary;
}

export interface ListItemsParams {
  q?: string;
  lowStock?: boolean;
  includeArchived?: boolean;
}

export interface CreateItemPayload {
  id: string;
  name: string;
  category?: string;
  unit: string;
  min_stock: number;
  sale_price_cents?: number;
  notes?: string;
  initial_stock?: number;
}

export interface UpdateItemPayload {
  name?: string;
  category?: string | null;
  unit?: string;
  min_stock?: number;
  sale_price_cents?: number | null;
  notes?: string | null;
}

export interface PutMovementPayload {
  item_id: string;
  kind: MovementKind;
  quantity: number;
  note?: string;
  occurred_at?: string;
}

function buildListQuery(params: ListItemsParams): string {
  const query = new URLSearchParams();
  if (params.q) {
    query.set("q", params.q);
  }
  if (params.lowStock) {
    query.set("low_stock", "true");
  }
  if (params.includeArchived) {
    query.set("include_archived", "true");
  }
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export const inventoryApi = {
  listItems: (params: ListItemsParams = {}) =>
    http.get<ItemOut[]>(`/api/inventory/items${buildListQuery(params)}`),
  getItem: (id: string) => http.get<ItemOut>(`/api/inventory/items/${id}`),
  createItem: (payload: CreateItemPayload) => http.post<ItemOut>("/api/inventory/items", payload),
  updateItem: (id: string, payload: UpdateItemPayload) =>
    http.patch<ItemOut>(`/api/inventory/items/${id}`, payload),
  archiveItem: (id: string) => http.post<void>(`/api/inventory/items/${id}/archive`),
  listMovements: (id: string, limit = 50) =>
    http.get<MovementOut[]>(`/api/inventory/items/${id}/movements?limit=${limit}`),
  putMovement: (movementId: string, payload: PutMovementPayload) =>
    http.put<MovementResult>(`/api/inventory/movements/${movementId}`, payload),
};

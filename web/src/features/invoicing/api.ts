import { http } from "../../shared/api/http";

/** `"01"` (Factura) in Phase A; `"06"` (Nota de Crédito) arrives in Phase B. */
export type DocumentType = "01" | "06";

export interface FiscalProfileOut {
  rtn: string;
  legal_name: string;
  trade_name: string;
  address: string;
  phone: string;
  email: string;
  establishment_code: string;
  emission_point_code: string;
  updated_at: string;
}

/** Every field is mandatory: `PUT /invoicing/profile` requires all of them (AD-3). */
export interface FiscalProfileSavePayload {
  rtn: string;
  legal_name: string;
  trade_name: string;
  address: string;
  phone: string;
  email: string;
  establishment_code: string;
  emission_point_code: string;
}

export interface DocumentReadinessOut {
  document_type: string;
  ready: boolean;
  blocked_reason: string | null;
  active_range_id: string | null;
  next_number: string | null;
}

export type CaiRangeState = "active" | "standby" | "exhausted" | "expired";

export interface CaiRangeOut {
  id: string;
  document_type: string;
  cai: string;
  establishment_code: string;
  emission_point_code: string;
  range_start: number;
  range_end: number;
  next_number: number;
  remaining: number;
  first_number: string;
  last_number: string;
  issue_deadline: string;
  state: CaiRangeState;
  in_use: boolean;
  created_at: string;
}

export interface InvoicingSettingsOut {
  profile: FiscalProfileOut | null;
  codes_locked: boolean;
  ranges: CaiRangeOut[];
  documents: DocumentReadinessOut[];
}

export interface CreateCaiRangePayload {
  id: string;
  document_type: DocumentType;
  cai: string;
  range_start: number;
  range_end: number;
  /** `YYYY-MM-DD`. */
  issue_deadline: string;
}

/** Every field optional (only a provided one is applied); none is nullable at the API. */
export interface UpdateCaiRangePayload {
  document_type?: DocumentType;
  cai?: string;
  range_start?: number;
  range_end?: number;
  issue_deadline?: string;
}

export const invoicingApi = {
  getSettings: () => http.get<InvoicingSettingsOut>("/api/invoicing/settings"),
  saveProfile: (payload: FiscalProfileSavePayload) =>
    http.put<FiscalProfileOut>("/api/invoicing/profile", payload),
  createCaiRange: (payload: CreateCaiRangePayload) =>
    http.post<CaiRangeOut>("/api/invoicing/cai-ranges", payload),
  updateCaiRange: (id: string, payload: UpdateCaiRangePayload) =>
    http.patch<CaiRangeOut>(`/api/invoicing/cai-ranges/${id}`, payload),
};

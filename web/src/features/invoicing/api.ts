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

export interface FiscalInvoiceLineOut {
  id: string;
  position: number;
  source_line_id: string;
  kind: string;
  description: string;
  quantity: number;
  unit_price_cents: number;
  line_total_cents: number;
}

/** A Factura's credit note reference, gained once it has been fully credited (phase B, AD-13). Mirrors the API's `CreditNoteRefOut`. */
export interface CreditNoteRefOut {
  id: string;
  number: string;
  issue_date: string;
}

/** The full Factura snapshot (AD-10): every field was copied at issuance and never recomputed on read. Mirrors the API's `FiscalInvoiceOut`. */
export interface FiscalInvoiceOut {
  id: string;
  order_id: string;
  order_number: number;
  number: string;
  issued_at: string;
  issue_date: string;
  issuer_rtn: string;
  issuer_legal_name: string;
  issuer_trade_name: string;
  issuer_address: string;
  issuer_phone: string;
  issuer_email: string;
  cai: string;
  range_first_number: string;
  range_last_number: string;
  issue_deadline: string;
  buyer_name: string | null;
  buyer_rtn: string | null;
  exempt_cents: number;
  exonerated_cents: number;
  discount_cents: number;
  taxable_15_cents: number;
  isv_15_cents: number;
  total_cents: number;
  total_in_words: string;
  credited_at: string | null;
  credit_note: CreditNoteRefOut | null;
  lines: FiscalInvoiceLineOut[];
  created_at: string;
}

/** The list shape for `GET /invoicing/invoices?order_id=`: no lines, matching the API's `FiscalInvoiceSummaryOut`. */
export interface FiscalInvoiceSummaryOut {
  id: string;
  number: string;
  issued_at: string;
  total_cents: number;
  credited_at: string | null;
  credit_note: CreditNoteRefOut | null;
}

export interface IssueInvoicePayload {
  id: string;
  order_id: string;
  buyer_name?: string;
  buyer_rtn?: string;
}

/** The full Nota de Crédito snapshot (AD-13): mirrors the API's `FiscalCreditNoteOut`. */
export interface FiscalCreditNoteOut {
  id: string;
  invoice_id: string;
  order_id: string;
  number: string;
  issued_at: string;
  issue_date: string;
  issuer_rtn: string;
  issuer_legal_name: string;
  issuer_trade_name: string;
  issuer_address: string;
  issuer_phone: string;
  issuer_email: string;
  cai: string;
  range_first_number: string;
  range_last_number: string;
  issue_deadline: string;
  buyer_name: string | null;
  buyer_rtn: string | null;
  original_cai: string;
  original_number: string;
  original_issue_date: string;
  reason: string;
  taxable_15_cents: number;
  isv_15_cents: number;
  total_cents: number;
  total_in_words: string;
  created_at: string;
}

export interface IssueCreditNotePayload {
  id: string;
  invoice_id: string;
  reason: string;
}

export const invoicingApi = {
  getSettings: () => http.get<InvoicingSettingsOut>("/api/invoicing/settings"),
  saveProfile: (payload: FiscalProfileSavePayload) =>
    http.put<FiscalProfileOut>("/api/invoicing/profile", payload),
  createCaiRange: (payload: CreateCaiRangePayload) =>
    http.post<CaiRangeOut>("/api/invoicing/cai-ranges", payload),
  updateCaiRange: (id: string, payload: UpdateCaiRangePayload) =>
    http.patch<CaiRangeOut>(`/api/invoicing/cai-ranges/${id}`, payload),
  issueInvoice: (payload: IssueInvoicePayload) =>
    http.post<FiscalInvoiceOut>("/api/invoicing/invoices", payload),
  getInvoice: (id: string) => http.get<FiscalInvoiceOut>(`/api/invoicing/invoices/${id}`),
  listOrderInvoices: (orderId: string) =>
    http.get<FiscalInvoiceSummaryOut[]>(`/api/invoicing/invoices?order_id=${orderId}`),
  issueCreditNote: (payload: IssueCreditNotePayload) =>
    http.post<FiscalCreditNoteOut>("/api/invoicing/credit-notes", payload),
  getCreditNote: (id: string) => http.get<FiscalCreditNoteOut>(`/api/invoicing/credit-notes/${id}`),
};

"""Pydantic schemas for the invoicing feature's HTTP surface."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, field_validator

from taller.invoicing.application.use_cases import DocumentReadiness, InvoicingSettings
from taller.invoicing.domain.document_number import DocumentNumber, DocumentType
from taller.invoicing.domain.documents import (
    FiscalCreditNote,
    FiscalInvoice,
    FiscalInvoiceLine,
)
from taller.invoicing.domain.profile import FiscalProfile
from taller.invoicing.domain.ranges import CaiRange, RangeState


class FiscalProfileSaveRequest(BaseModel):
    """Every field is mandatory: Art. 10-11 requires all of them on
    every printed document, so a stored profile is always complete
    (AD-3). Pydantic already rejects an explicit ``null`` for any of
    these -- none is declared optional.
    """

    rtn: str
    legal_name: str
    trade_name: str
    address: str
    phone: str
    email: str
    establishment_code: str
    emission_point_code: str


class FiscalProfileOut(BaseModel):
    rtn: str
    legal_name: str
    trade_name: str
    address: str
    phone: str
    email: str
    establishment_code: str
    emission_point_code: str
    updated_at: datetime

    @classmethod
    def from_domain(cls, profile: FiscalProfile) -> "FiscalProfileOut":
        return cls(
            rtn=profile.rtn,
            legal_name=profile.legal_name,
            trade_name=profile.trade_name,
            address=profile.address,
            phone=profile.phone,
            email=profile.email,
            establishment_code=profile.establishment_code,
            emission_point_code=profile.emission_point_code,
            updated_at=profile.updated_at,
        )


class DocumentReadinessOut(BaseModel):
    document_type: str
    ready: bool
    blocked_reason: str | None
    active_range_id: uuid.UUID | None
    next_number: str | None

    @classmethod
    def from_domain(cls, readiness: DocumentReadiness) -> "DocumentReadinessOut":
        return cls(
            document_type=readiness.document_type.value,
            ready=readiness.ready,
            blocked_reason=readiness.blocked_reason,
            active_range_id=readiness.active_range_id,
            next_number=readiness.next_number,
        )


class CaiRangeOut(BaseModel):
    id: uuid.UUID
    document_type: str
    cai: str
    establishment_code: str
    emission_point_code: str
    range_start: int
    range_end: int
    next_number: int
    remaining: int
    first_number: str
    last_number: str
    issue_deadline: date
    state: str
    in_use: bool
    created_at: datetime

    @classmethod
    def from_domain(cls, cai_range: CaiRange, *, state: RangeState) -> "CaiRangeOut":
        return cls(
            id=cai_range.id,
            document_type=cai_range.document_type.value,
            cai=cai_range.cai,
            establishment_code=cai_range.establishment_code,
            emission_point_code=cai_range.emission_point_code,
            range_start=cai_range.range_start,
            range_end=cai_range.range_end,
            next_number=cai_range.next_number,
            remaining=cai_range.remaining,
            first_number=str(
                DocumentNumber(
                    establishment=cai_range.establishment_code,
                    emission_point=cai_range.emission_point_code,
                    document_type=cai_range.document_type,
                    correlative=cai_range.range_start,
                )
            ),
            last_number=str(
                DocumentNumber(
                    establishment=cai_range.establishment_code,
                    emission_point=cai_range.emission_point_code,
                    document_type=cai_range.document_type,
                    correlative=cai_range.range_end,
                )
            ),
            issue_deadline=cai_range.issue_deadline,
            state=state.value,
            in_use=cai_range.in_use,
            created_at=cai_range.created_at,
        )


class CaiRangeCreateRequest(BaseModel):
    id: uuid.UUID
    document_type: DocumentType
    cai: str
    range_start: int
    range_end: int
    issue_deadline: date


class CaiRangePatchRequest(BaseModel):
    """Every field is optional (only a provided one is applied), but
    none of them is nullable at the domain level, so an explicit
    ``null`` is rejected rather than silently applying no change.
    """

    document_type: DocumentType | None = None
    cai: str | None = None
    range_start: int | None = None
    range_end: int | None = None
    issue_deadline: date | None = None

    @field_validator("document_type")
    @classmethod
    def _reject_null_document_type(cls, value: DocumentType | None) -> DocumentType:
        if value is None:
            raise ValueError("document_type cannot be null")
        return value

    @field_validator("cai")
    @classmethod
    def _reject_null_cai(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("cai cannot be null")
        return value

    @field_validator("range_start")
    @classmethod
    def _reject_null_range_start(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("range_start cannot be null")
        return value

    @field_validator("range_end")
    @classmethod
    def _reject_null_range_end(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("range_end cannot be null")
        return value

    @field_validator("issue_deadline")
    @classmethod
    def _reject_null_issue_deadline(cls, value: date | None) -> date:
        if value is None:
            raise ValueError("issue_deadline cannot be null")
        return value


class InvoicingSettingsOut(BaseModel):
    profile: FiscalProfileOut | None
    codes_locked: bool
    ranges: list[CaiRangeOut]
    documents: list[DocumentReadinessOut]

    @classmethod
    def from_domain(cls, settings: InvoicingSettings) -> "InvoicingSettingsOut":
        return cls(
            profile=FiscalProfileOut.from_domain(settings.profile) if settings.profile else None,
            codes_locked=settings.codes_locked,
            ranges=[
                CaiRangeOut.from_domain(r, state=settings.range_states[r.id])
                for r in settings.ranges
            ],
            documents=[DocumentReadinessOut.from_domain(d) for d in settings.documents],
        )


class FiscalInvoiceCreateRequest(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    buyer_name: str | None = None
    buyer_rtn: str | None = None


class CreditNoteRefOut(BaseModel):
    """The credit note reference a Factura's response gains once it has
    been fully credited (phase B, AD-13).
    """

    id: uuid.UUID
    number: str
    issue_date: date

    @classmethod
    def from_domain(cls, credit_note: FiscalCreditNote) -> "CreditNoteRefOut":
        return cls(id=credit_note.id, number=credit_note.number, issue_date=credit_note.issue_date)


class FiscalInvoiceLineOut(BaseModel):
    id: uuid.UUID
    position: int
    source_line_id: uuid.UUID
    kind: str
    description: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int

    @classmethod
    def from_domain(cls, line: FiscalInvoiceLine) -> "FiscalInvoiceLineOut":
        return cls(
            id=line.id,
            position=line.position,
            source_line_id=line.source_line_id,
            kind=line.kind,
            description=line.description,
            quantity=line.quantity,
            unit_price_cents=line.unit_price_cents,
            line_total_cents=line.line_total_cents,
        )


class FiscalInvoiceOut(BaseModel):
    """The full Factura snapshot (AD-10): every field is copied at
    issuance and never recomputed on read, so a later profile or
    customer edit never changes what an already-issued document shows.
    """

    id: uuid.UUID
    order_id: uuid.UUID
    order_number: int
    number: str
    issued_at: datetime
    issue_date: date
    issuer_rtn: str
    issuer_legal_name: str
    issuer_trade_name: str
    issuer_address: str
    issuer_phone: str
    issuer_email: str
    cai: str
    range_first_number: str
    range_last_number: str
    issue_deadline: date
    buyer_name: str | None
    buyer_rtn: str | None
    exempt_cents: int
    exonerated_cents: int
    discount_cents: int
    taxable_15_cents: int
    isv_15_cents: int
    total_cents: int
    total_in_words: str
    credited_at: datetime | None
    credit_note: CreditNoteRefOut | None
    lines: list[FiscalInvoiceLineOut]
    created_at: datetime

    @classmethod
    def from_domain(
        cls, invoice: FiscalInvoice, *, credit_note: FiscalCreditNote | None = None
    ) -> "FiscalInvoiceOut":
        return cls(
            id=invoice.id,
            order_id=invoice.order_id,
            order_number=invoice.order_number,
            number=invoice.number,
            issued_at=invoice.issued_at,
            issue_date=invoice.issue_date,
            issuer_rtn=invoice.issuer_rtn,
            issuer_legal_name=invoice.issuer_legal_name,
            issuer_trade_name=invoice.issuer_trade_name,
            issuer_address=invoice.issuer_address,
            issuer_phone=invoice.issuer_phone,
            issuer_email=invoice.issuer_email,
            cai=invoice.cai,
            range_first_number=invoice.range_first_number,
            range_last_number=invoice.range_last_number,
            issue_deadline=invoice.issue_deadline,
            buyer_name=invoice.buyer_name,
            buyer_rtn=invoice.buyer_rtn,
            exempt_cents=invoice.exempt_cents,
            exonerated_cents=invoice.exonerated_cents,
            discount_cents=invoice.discount_cents,
            taxable_15_cents=invoice.taxable_15_cents,
            isv_15_cents=invoice.isv_15_cents,
            total_cents=invoice.total_cents,
            total_in_words=invoice.total_in_words,
            credited_at=invoice.credited_at,
            credit_note=CreditNoteRefOut.from_domain(credit_note) if credit_note else None,
            lines=[FiscalInvoiceLineOut.from_domain(line) for line in invoice.lines],
            created_at=invoice.created_at,
        )


class FiscalInvoiceSummaryOut(BaseModel):
    """The list shape for `GET /invoicing/invoices?order_id=`: no lines,
    matching every other summary schema in this codebase.
    """

    id: uuid.UUID
    number: str
    issued_at: datetime
    total_cents: int
    credited_at: datetime | None
    credit_note: CreditNoteRefOut | None

    @classmethod
    def from_domain(
        cls, invoice: FiscalInvoice, *, credit_note: FiscalCreditNote | None = None
    ) -> "FiscalInvoiceSummaryOut":
        return cls(
            id=invoice.id,
            number=invoice.number,
            issued_at=invoice.issued_at,
            total_cents=invoice.total_cents,
            credited_at=invoice.credited_at,
            credit_note=CreditNoteRefOut.from_domain(credit_note) if credit_note else None,
        )


class FiscalCreditNoteCreateRequest(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    reason: str


class FiscalCreditNoteOut(BaseModel):
    """The full Nota de Credito snapshot (AD-13): every field is copied
    at issuance and never recomputed on read, so a later profile or
    customer edit never changes what an already-issued document shows.
    """

    id: uuid.UUID
    invoice_id: uuid.UUID
    order_id: uuid.UUID
    number: str
    issued_at: datetime
    issue_date: date
    issuer_rtn: str
    issuer_legal_name: str
    issuer_trade_name: str
    issuer_address: str
    issuer_phone: str
    issuer_email: str
    cai: str
    range_first_number: str
    range_last_number: str
    issue_deadline: date
    buyer_name: str | None
    buyer_rtn: str | None
    original_cai: str
    original_number: str
    original_issue_date: date
    reason: str
    taxable_15_cents: int
    isv_15_cents: int
    total_cents: int
    total_in_words: str
    created_at: datetime

    @classmethod
    def from_domain(cls, credit_note: FiscalCreditNote) -> "FiscalCreditNoteOut":
        return cls(
            id=credit_note.id,
            invoice_id=credit_note.invoice_id,
            order_id=credit_note.order_id,
            number=credit_note.number,
            issued_at=credit_note.issued_at,
            issue_date=credit_note.issue_date,
            issuer_rtn=credit_note.issuer_rtn,
            issuer_legal_name=credit_note.issuer_legal_name,
            issuer_trade_name=credit_note.issuer_trade_name,
            issuer_address=credit_note.issuer_address,
            issuer_phone=credit_note.issuer_phone,
            issuer_email=credit_note.issuer_email,
            cai=credit_note.cai,
            range_first_number=credit_note.range_first_number,
            range_last_number=credit_note.range_last_number,
            issue_deadline=credit_note.issue_deadline,
            buyer_name=credit_note.buyer_name,
            buyer_rtn=credit_note.buyer_rtn,
            original_cai=credit_note.original_cai,
            original_number=credit_note.original_number,
            original_issue_date=credit_note.original_issue_date,
            reason=credit_note.reason,
            taxable_15_cents=credit_note.taxable_15_cents,
            isv_15_cents=credit_note.isv_15_cents,
            total_cents=credit_note.total_cents,
            total_in_words=credit_note.total_in_words,
            created_at=credit_note.created_at,
        )

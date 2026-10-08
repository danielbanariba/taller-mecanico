"""Pydantic schemas for the invoicing feature's HTTP surface."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, field_validator

from taller.invoicing.application.use_cases import DocumentReadiness, InvoicingSettings
from taller.invoicing.domain.document_number import DocumentNumber, DocumentType
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

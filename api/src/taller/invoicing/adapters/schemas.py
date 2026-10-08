"""Pydantic schemas for the invoicing feature's HTTP surface."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from taller.invoicing.application.use_cases import DocumentReadiness, InvoicingSettings
from taller.invoicing.domain.profile import FiscalProfile


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


class InvoicingSettingsOut(BaseModel):
    """`ranges` (the full `CaiRangeOut[]` listing) is added in `PA.S4`
    once CAI range registration exists; this slice only serves the
    readiness `GET /invoicing/settings` and the order detail need.
    """

    profile: FiscalProfileOut | None
    codes_locked: bool
    documents: list[DocumentReadinessOut]

    @classmethod
    def from_domain(cls, settings: InvoicingSettings) -> "InvoicingSettingsOut":
        return cls(
            profile=FiscalProfileOut.from_domain(settings.profile) if settings.profile else None,
            codes_locked=settings.codes_locked,
            documents=[DocumentReadinessOut.from_domain(d) for d in settings.documents],
        )

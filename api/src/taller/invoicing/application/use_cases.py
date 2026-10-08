"""Use cases for the invoicing feature: the fiscal profile and the
shared invoicing readiness `GET /invoicing/settings` serves (AD-3,
AD-4, AD-6).
"""

import uuid
from dataclasses import dataclass
from datetime import date

from taller.customers.domain.rtn import Rtn
from taller.identity.application.ports import Clock
from taller.identity.domain.phone_number import PhoneNumber
from taller.invoicing.application.ports import CaiRangeRepository, FiscalProfileRepository
from taller.invoicing.domain.document_number import DocumentNumber, DocumentType
from taller.invoicing.domain.errors import FiscalProfileCodesLocked
from taller.invoicing.domain.profile import (
    FiscalProfile,
    normalize_email,
    normalize_emission_point_code,
    normalize_establishment_code,
)
from taller.invoicing.domain.ranges import CaiRange, RangeState, range_states
from taller.shared.timezone import local_today

#: Phase A only ever asks about the Factura document type; Phase B
#: adds `06` to this list once credit notes exist.
_READY_DOCUMENT_TYPES: tuple[DocumentType, ...] = (DocumentType.invoice,)


def save_profile(
    *,
    workshop_id: uuid.UUID,
    rtn: str,
    legal_name: str,
    trade_name: str,
    address: str,
    phone: str,
    email: str,
    establishment_code: str,
    emission_point_code: str,
    clock: Clock,
    profile_repo: FiscalProfileRepository,
    range_repo: CaiRangeRepository,
) -> tuple[FiscalProfile, bool]:
    """Save a workshop's fiscal profile: an idempotent upsert keyed by
    the workshop, since every field is mandatory on every save (AD-3).

    Returns ``(profile, is_new)``: ``is_new`` is False when a profile
    already existed for this workshop (the caller should respond 200,
    not 201).

    Raises:
        InvalidRtn / InvalidPhoneNumber / InvalidEmail /
            InvalidEstablishmentCode / InvalidEmissionPointCode: a
            field fails its own validation.
        FiscalProfileCodesLocked: the establecimiento or punto de
            emisión code would change while a usable CAI range exists.
    """
    normalized_rtn = Rtn.from_raw(rtn)
    normalized_legal_name = legal_name.strip()
    normalized_trade_name = trade_name.strip()
    normalized_address = address.strip()
    normalized_phone = PhoneNumber.from_raw(phone).value
    normalized_email = normalize_email(email)
    normalized_establishment = normalize_establishment_code(establishment_code)
    normalized_emission_point = normalize_emission_point_code(emission_point_code)

    existing = profile_repo.get_for_update(workshop_id=workshop_id)
    now = clock.now()

    if existing is not None:
        codes_changed = (
            existing.establishment_code != normalized_establishment
            or existing.emission_point_code != normalized_emission_point
        )
        if codes_changed:
            today = local_today(clock)
            ranges = range_repo.list(workshop_id=workshop_id)
            if any(r.usable_on(today) for r in ranges):
                raise FiscalProfileCodesLocked(workshop_id)

        existing.rtn = normalized_rtn
        existing.legal_name = normalized_legal_name
        existing.trade_name = normalized_trade_name
        existing.address = normalized_address
        existing.phone = normalized_phone
        existing.email = normalized_email
        existing.establishment_code = normalized_establishment
        existing.emission_point_code = normalized_emission_point
        existing.updated_at = now
        profile_repo.save(existing)
        return existing, False

    profile = FiscalProfile(
        workshop_id=workshop_id,
        rtn=normalized_rtn,
        legal_name=normalized_legal_name,
        trade_name=normalized_trade_name,
        address=normalized_address,
        phone=normalized_phone,
        email=normalized_email,
        establishment_code=normalized_establishment,
        emission_point_code=normalized_emission_point,
        created_at=now,
        updated_at=now,
    )
    profile_repo.add(profile)
    return profile, True


@dataclass(frozen=True, slots=True)
class DocumentReadiness:
    """Whether a document type can be issued right now, and why not
    when it can't -- the same predicate `GET /invoicing/settings` and
    issuance both read (AD-3), so they can never disagree.
    """

    document_type: DocumentType
    ready: bool
    blocked_reason: str | None
    active_range_id: uuid.UUID | None
    next_number: str | None


@dataclass(frozen=True, slots=True)
class InvoicingSettings:
    profile: FiscalProfile | None
    codes_locked: bool
    documents: list[DocumentReadiness]


def _document_readiness(
    *,
    document_type: DocumentType,
    profile: FiscalProfile | None,
    ranges: list[CaiRange],
    today: date,
) -> DocumentReadiness:
    if profile is None or not profile.is_complete:
        return DocumentReadiness(
            document_type=document_type,
            ready=False,
            blocked_reason="fiscal_profile_missing",
            active_range_id=None,
            next_number=None,
        )

    states = range_states(ranges, today)
    active = next((r for r in ranges if states.get(r.id) == RangeState.active), None)
    if active is not None:
        number = DocumentNumber(
            establishment=profile.establishment_code,
            emission_point=profile.emission_point_code,
            document_type=document_type,
            correlative=active.next_number,
        )
        return DocumentReadiness(
            document_type=document_type,
            ready=True,
            blocked_reason=None,
            active_range_id=active.id,
            next_number=str(number),
        )

    if not ranges:
        blocked_reason = "cai_range_missing"
    elif any(r.remaining > 0 for r in ranges):
        blocked_reason = "cai_range_expired"
    else:
        blocked_reason = "cai_range_exhausted"

    return DocumentReadiness(
        document_type=document_type,
        ready=False,
        blocked_reason=blocked_reason,
        active_range_id=None,
        next_number=None,
    )


def get_settings(
    *,
    workshop_id: uuid.UUID,
    clock: Clock,
    profile_repo: FiscalProfileRepository,
    range_repo: CaiRangeRepository,
) -> InvoicingSettings:
    """The workshop's fiscal profile plus per-document-type readiness
    (AD-3, AD-4): the same information the order detail's "Emitir
    factura" gate reads.
    """
    profile = profile_repo.get(workshop_id=workshop_id)
    today = local_today(clock)

    all_ranges = range_repo.list(workshop_id=workshop_id)
    codes_locked = profile is not None and any(r.usable_on(today) for r in all_ranges)

    documents = [
        _document_readiness(
            document_type=document_type,
            profile=profile,
            ranges=[r for r in all_ranges if r.document_type == document_type],
            today=today,
        )
        for document_type in _READY_DOCUMENT_TYPES
    ]
    return InvoicingSettings(profile=profile, codes_locked=codes_locked, documents=documents)

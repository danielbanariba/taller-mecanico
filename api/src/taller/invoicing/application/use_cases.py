"""Use cases for the invoicing feature: the fiscal profile and the
shared invoicing readiness `GET /invoicing/settings` serves (AD-3,
AD-4, AD-6).
"""

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Final

from taller.customers.domain.rtn import Rtn
from taller.identity.application.ports import Clock
from taller.identity.domain.phone_number import PhoneNumber
from taller.invoicing.application.ports import (
    CaiRangeRepository,
    CreditNoteRepository,
    FiscalInvoiceRepository,
    FiscalProfileRepository,
)
from taller.invoicing.domain.amount_in_words import MAX_LEMPIRAS, amount_in_words
from taller.invoicing.domain.buyer import resolve_buyer
from taller.invoicing.domain.document_number import DocumentNumber, DocumentType
from taller.invoicing.domain.documents import (
    FiscalCreditNote,
    FiscalInvoice,
    FiscalInvoiceLine,
    fiscal_invoice_line_id,
)
from taller.invoicing.domain.errors import (
    BuyerNameRequired,
    CaiRangeExhausted,
    CaiRangeIdConflict,
    CaiRangeImmutable,
    CaiRangeNotFound,
    CaiRangeOverlap,
    CreditNoteIdConflict,
    CreditNoteNotFound,
    FiscalInvoiceIdConflict,
    FiscalInvoiceNotFound,
    FiscalProfileCodesLocked,
    FiscalProfileMissing,
    InvalidCreditNoteReason,
    InvoiceAlreadyCredited,
    InvoiceAmountTooLarge,
    InvoiceAmountZero,
    WorkOrderAlreadyInvoiced,
    WorkOrderNotInvoiceable,
)
from taller.invoicing.domain.profile import (
    FiscalProfile,
    normalize_email,
    normalize_emission_point_code,
    normalize_establishment_code,
)
from taller.invoicing.domain.ranges import (
    CaiRange,
    RangeState,
    RangeWarning,
    normalize_cai,
    overlaps,
    range_states,
    range_warnings,
    select_range,
    validate_issue_deadline,
    validate_range_bounds,
)
from taller.invoicing.domain.tax import split_tax_inclusive_total
from taller.shared.timezone import HONDURAS_TZ, local_today
from taller.workorders.application.ports import WorkOrderRepository
from taller.workorders.domain.errors import WorkOrderNotFound
from taller.workorders.domain.money import line_subtotal_cents, order_total_cents
from taller.workorders.domain.status import WorkOrderStatus

#: An order in either of these statuses may be invoiced (`fiscal-invoices`
#: spec): work still open (`quote`, `approved`, `in_progress`) is excluded.
#: `cancelled` is unreachable from `completed`/`delivered` in `TRANSITIONS`,
#: so this set can never include a cancelled order either.
INVOICEABLE: Final[frozenset[WorkOrderStatus]] = frozenset(
    {WorkOrderStatus.completed, WorkOrderStatus.delivered}
)

#: `amount_in_words`'s own bound, in cents (AD-6, AD-9): checked before the
#: words function ever runs, so an out-of-range total is a clear domain
#: error instead of propagating `AmountInWordsOutOfRange` from deep inside
#: snapshot construction.
MAX_INVOICE_CENTS: Final = MAX_LEMPIRAS * 100

#: Phase A only ever asked about the Factura document type; phase B adds
#: `06` now that credit notes exist, so `GET /invoicing/settings` reports
#: both documents' readiness.
_READY_DOCUMENT_TYPES: tuple[DocumentType, ...] = (DocumentType.invoice, DocumentType.credit_note)

#: A credit note's reason (AD-13): trimmed, 1-300 characters.
MAX_CREDIT_NOTE_REASON_LENGTH: Final = 300


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
    warnings: list[RangeWarning]


@dataclass(frozen=True, slots=True)
class InvoicingSettings:
    profile: FiscalProfile | None
    codes_locked: bool
    ranges: list[CaiRange]
    range_states: dict[uuid.UUID, RangeState]
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
            warnings=[],
        )

    # AD-18: warnings are evaluated over this document type's own
    # ranges regardless of readiness, so a workshop still sees "act
    # now" even while a range is merely standby, not yet active.
    warnings = range_warnings(ranges, today)

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
            warnings=warnings,
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
        warnings=warnings,
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
    return InvoicingSettings(
        profile=profile,
        codes_locked=codes_locked,
        ranges=all_ranges,
        range_states=range_states(all_ranges, today),
        documents=documents,
    )


def _range_fields_match(
    existing: CaiRange,
    *,
    document_type: DocumentType,
    cai: str,
    range_start: int,
    range_end: int,
    issue_deadline: date,
) -> bool:
    return (
        existing.document_type == document_type
        and existing.cai == cai
        and existing.range_start == range_start
        and existing.range_end == range_end
        and existing.issue_deadline == issue_deadline
    )


def create_range(
    *,
    workshop_id: uuid.UUID,
    range_id: uuid.UUID,
    document_type: DocumentType,
    cai: str,
    range_start: int,
    range_end: int,
    issue_deadline: date,
    created_by: uuid.UUID,
    clock: Clock,
    profile_repo: FiscalProfileRepository,
    range_repo: CaiRangeRepository,
) -> tuple[CaiRange, bool]:
    """Register a CAI range, or replay an idempotent registration
    (AD-4): the establecimiento and punto de emisión codes are always
    copied from the workshop's fiscal profile at registration, so a
    later profile edit never changes an already-registered range's
    printed codes.

    Returns ``(cai_range, is_new)``: ``is_new`` is False when
    ``range_id`` already existed with identical fields (the caller
    should respond 200, not 201).

    Raises:
        InvalidCai / InvalidCaiRange / CaiDeadlinePassed /
            CaiDeadlineTooFar: a field fails its own validation.
        CaiRangeIdConflict: ``range_id`` already exists with different
            fields.
        FiscalProfileMissing: the workshop has no fiscal profile yet.
        CaiRangeOverlap: the bounds intersect another range of the
            same workshop, document type, establecimiento and punto
            de emisión.
    """
    normalized_cai = normalize_cai(cai)
    validate_range_bounds(range_start=range_start, range_end=range_end)
    today = local_today(clock)
    validate_issue_deadline(issue_deadline, today=today)

    existing = range_repo.get_by_id(workshop_id=workshop_id, range_id=range_id)
    if existing is not None:
        if not _range_fields_match(
            existing,
            document_type=document_type,
            cai=normalized_cai,
            range_start=range_start,
            range_end=range_end,
            issue_deadline=issue_deadline,
        ):
            raise CaiRangeIdConflict(range_id)
        return existing, False

    profile = profile_repo.get_for_update(workshop_id=workshop_id)
    if profile is None:
        raise FiscalProfileMissing()

    now = clock.now()
    candidate = CaiRange(
        id=range_id,
        workshop_id=workshop_id,
        document_type=document_type,
        cai=normalized_cai,
        establishment_code=profile.establishment_code,
        emission_point_code=profile.emission_point_code,
        range_start=range_start,
        range_end=range_end,
        next_number=range_start,
        issue_deadline=issue_deadline,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    siblings = range_repo.list(workshop_id=workshop_id, document_type=document_type)
    if overlaps(candidate, siblings):
        raise CaiRangeOverlap(range_id)

    range_repo.add(candidate)
    return candidate, True


def update_range(
    *,
    workshop_id: uuid.UUID,
    range_id: uuid.UUID,
    fields: dict,
    clock: Clock,
    profile_repo: FiscalProfileRepository,
    range_repo: CaiRangeRepository,
) -> CaiRange:
    """Correct an unused CAI range's fields (AD-4): a mistyped CAI or
    deadline is the likeliest error, and it would otherwise be printed
    on a legal document. Locks the workshop's fiscal profile first
    (AD-5) -- the same per-workshop mutex every other invoicing write
    takes -- so two concurrent range writes still serialize the
    overlap check below.

    Raises:
        FiscalProfileMissing: the workshop has no fiscal profile
            (defensive: a range cannot exist without one).
        CaiRangeNotFound: no such range in this workshop.
        CaiRangeImmutable: at least one number has already been
            allocated from this range.
        InvalidCai / InvalidCaiRange / CaiDeadlinePassed /
            CaiDeadlineTooFar: a new field value fails its own
            validation.
        CaiRangeOverlap: the new bounds intersect another range of the
            resulting document type, establecimiento and punto de
            emisión.
    """
    cai_range = range_repo.get_by_id(workshop_id=workshop_id, range_id=range_id)
    if cai_range is None:
        raise CaiRangeNotFound(range_id)

    profile = profile_repo.get_for_update(workshop_id=workshop_id)
    if profile is None:
        raise FiscalProfileMissing()

    # Re-read the range now that the profile mutex (AD-5) is held: the
    # snapshot fetched above, before the lock, can already be stale --
    # a concurrent issue_invoice() may have allocated a number from this
    # range in the window between that read and this lock, and the
    # immutability check below must see that allocation, not the
    # pre-lock state, or it would un-consume an already-issued Factura's
    # correlative.
    cai_range = range_repo.get_by_id(workshop_id=workshop_id, range_id=range_id)
    if cai_range is None:
        raise CaiRangeNotFound(range_id)
    if cai_range.in_use:
        raise CaiRangeImmutable(range_id)

    # Phase B accepts both `01` and `06` (D2); no document-type gate
    # applies here, mirroring `create_range`'s own phase B change.
    document_type = fields.get("document_type", cai_range.document_type)

    cai = normalize_cai(fields["cai"]) if "cai" in fields else cai_range.cai
    range_start = fields.get("range_start", cai_range.range_start)
    range_end = fields.get("range_end", cai_range.range_end)
    validate_range_bounds(range_start=range_start, range_end=range_end)

    issue_deadline = fields.get("issue_deadline", cai_range.issue_deadline)
    today = local_today(clock)
    validate_issue_deadline(issue_deadline, today=today)

    cai_range.document_type = document_type
    cai_range.cai = cai
    cai_range.range_start = range_start
    cai_range.range_end = range_end
    # Still unused (just confirmed above), so next_number tracks range_start.
    cai_range.next_number = range_start
    cai_range.issue_deadline = issue_deadline
    cai_range.updated_at = clock.now()

    siblings = range_repo.list(workshop_id=workshop_id, document_type=document_type)
    if overlaps(cai_range, siblings):
        raise CaiRangeOverlap(range_id)

    range_repo.save(cai_range)
    return cai_range


def _invoice_fields_match(
    existing: FiscalInvoice,
    *,
    order_id: uuid.UUID,
    buyer_name: str | None,
    buyer_rtn: str | None,
) -> bool:
    return (
        existing.order_id == order_id
        and existing.buyer_name == buyer_name
        and existing.buyer_rtn == buyer_rtn
    )


def issue_invoice(
    *,
    workshop_id: uuid.UUID,
    invoice_id: uuid.UUID,
    order_id: uuid.UUID,
    buyer_name: str | None,
    buyer_rtn: str | None,
    created_by: uuid.UUID,
    clock: Clock,
    order_repo: WorkOrderRepository,
    profile_repo: FiscalProfileRepository,
    range_repo: CaiRangeRepository,
    invoice_repo: FiscalInvoiceRepository,
) -> tuple[FiscalInvoice, bool]:
    """Issue a Factura from an eligible work order, or replay an
    idempotent issuance (AD-6's eight steps: normalize buyer, lock
    order, replay, eligibility, lock profile, select+allocate range,
    build+insert snapshot).

    Returns ``(invoice, is_new)``: ``is_new`` is False when
    ``invoice_id`` already existed with identical fields (the caller
    should respond 200, not 201).

    Raises:
        InvalidRtn: ``buyer_rtn`` fails its own format validation.
        BuyerNameRequired: ``buyer_rtn`` is supplied without
            ``buyer_name``.
        WorkOrderNotFound: no such order in this workshop.
        FiscalInvoiceIdConflict: ``invoice_id`` already exists with
            fields that do not match this request.
        WorkOrderNotInvoiceable: the order's status is not
            `completed` or `delivered`.
        WorkOrderAlreadyInvoiced: the order already has a
            non-credited Factura.
        InvoiceAmountZero / InvoiceAmountTooLarge: the order's total
            is outside the issuable range.
        BuyerIdentificationRequired: the total is at or above the
            identification threshold and buyer data is incomplete
            (AD-11).
        FiscalProfileMissing: the workshop has no fiscal profile.
        CaiRangeMissing / CaiRangeExpired / CaiRangeExhausted: no `01`
            range is usable today (AD-4, AD-6).
    """
    normalized_rtn = Rtn.from_raw(buyer_rtn) if buyer_rtn is not None else None
    if normalized_rtn is not None and buyer_name is None:
        raise BuyerNameRequired()
    normalized_name = buyer_name.strip() if buyer_name is not None else None

    order = order_repo.get_for_update(workshop_id=workshop_id, order_id=order_id)
    if order is None:
        raise WorkOrderNotFound(order_id)

    existing = invoice_repo.get_by_id(workshop_id=workshop_id, invoice_id=invoice_id)
    if existing is not None:
        if not _invoice_fields_match(
            existing, order_id=order_id, buyer_name=normalized_name, buyer_rtn=normalized_rtn
        ):
            raise FiscalInvoiceIdConflict(invoice_id)
        return existing, False

    if order.status not in INVOICEABLE:
        raise WorkOrderNotInvoiceable(order_id)
    if invoice_repo.has_active_for_order(workshop_id=workshop_id, order_id=order_id):
        raise WorkOrderAlreadyInvoiced(order_id)

    total_cents = order_total_cents(order.lines)
    if total_cents <= 0:
        raise InvoiceAmountZero(order_id)
    if total_cents > MAX_INVOICE_CENTS:
        raise InvoiceAmountTooLarge(total_cents)

    buyer = resolve_buyer(name=normalized_name, rtn=normalized_rtn, total_cents=total_cents)

    profile = profile_repo.get_for_update(workshop_id=workshop_id)
    if profile is None:
        raise FiscalProfileMissing()

    now = clock.now()
    today = now.astimezone(HONDURAS_TZ).date()
    ranges = range_repo.list(workshop_id=workshop_id, document_type=DocumentType.invoice)
    cai_range = select_range(ranges, today)

    correlative = range_repo.allocate(range_id=cai_range.id, now=now)
    if correlative is None:
        # The profile lock serializes every fiscal write for this workshop,
        # so another allocation emptying the range between `select_range`
        # and here should never actually happen -- but fail safely as
        # exhausted rather than crash if it somehow does.
        raise CaiRangeExhausted()

    number = DocumentNumber(
        establishment=profile.establishment_code,
        emission_point=profile.emission_point_code,
        document_type=DocumentType.invoice,
        correlative=correlative,
    )
    amounts = split_tax_inclusive_total(total_cents)
    ordered_lines = [line for line in order.lines if line.removed_at is None]
    invoice_lines = [
        FiscalInvoiceLine(
            id=fiscal_invoice_line_id(invoice_id, position),
            position=position,
            source_line_id=line.id,
            kind=line.kind.value,
            description=line.description,
            quantity=line.quantity,
            unit_price_cents=line.unit_price_cents,
            line_total_cents=line_subtotal_cents(line),
        )
        for position, line in enumerate(ordered_lines, start=1)
    ]

    invoice = FiscalInvoice(
        id=invoice_id,
        workshop_id=workshop_id,
        order_id=order_id,
        order_number=order.number,
        cai_range_id=cai_range.id,
        correlative=correlative,
        number=str(number),
        issued_at=now,
        issue_date=today,
        issuer_rtn=profile.rtn,
        issuer_legal_name=profile.legal_name,
        issuer_trade_name=profile.trade_name,
        issuer_address=profile.address,
        issuer_phone=profile.phone,
        issuer_email=profile.email,
        cai=cai_range.cai,
        range_first_number=str(
            DocumentNumber(
                establishment=cai_range.establishment_code,
                emission_point=cai_range.emission_point_code,
                document_type=cai_range.document_type,
                correlative=cai_range.range_start,
            )
        ),
        range_last_number=str(
            DocumentNumber(
                establishment=cai_range.establishment_code,
                emission_point=cai_range.emission_point_code,
                document_type=cai_range.document_type,
                correlative=cai_range.range_end,
            )
        ),
        issue_deadline=cai_range.issue_deadline,
        buyer_name=buyer.name,
        buyer_rtn=buyer.rtn,
        exempt_cents=amounts.exempt_cents,
        exonerated_cents=amounts.exonerated_cents,
        discount_cents=amounts.discount_cents,
        taxable_15_cents=amounts.taxable_15_cents,
        isv_15_cents=amounts.isv_15_cents,
        total_cents=amounts.total_cents,
        total_in_words=amount_in_words(total_cents),
        credited_at=None,
        created_by=created_by,
        created_at=now,
        lines=invoice_lines,
    )
    invoice_repo.add(invoice)
    return invoice, True


def get_invoice(
    *, workshop_id: uuid.UUID, invoice_id: uuid.UUID, invoice_repo: FiscalInvoiceRepository
) -> FiscalInvoice:
    """Raises: FiscalInvoiceNotFound: no such invoice in this workshop."""
    invoice = invoice_repo.get_by_id(workshop_id=workshop_id, invoice_id=invoice_id)
    if invoice is None:
        raise FiscalInvoiceNotFound(invoice_id)
    return invoice


def list_order_invoices(
    *, workshop_id: uuid.UUID, order_id: uuid.UUID, invoice_repo: FiscalInvoiceRepository
) -> list[FiscalInvoice]:
    """Every Factura issued for this order, newest first, credited ones included."""
    return invoice_repo.list_for_order(workshop_id=workshop_id, order_id=order_id)


def _normalize_credit_note_reason(raw: str) -> str:
    """Raises: InvalidCreditNoteReason: ``raw`` is empty after trimming,
    or exceeds `MAX_CREDIT_NOTE_REASON_LENGTH` characters (AD-13).
    """
    trimmed = raw.strip()
    if not trimmed or len(trimmed) > MAX_CREDIT_NOTE_REASON_LENGTH:
        raise InvalidCreditNoteReason(raw)
    return trimmed


def _credit_note_fields_match(
    existing: FiscalCreditNote, *, invoice_id: uuid.UUID, reason: str
) -> bool:
    return existing.invoice_id == invoice_id and existing.reason == reason


def issue_credit_note(
    *,
    workshop_id: uuid.UUID,
    credit_note_id: uuid.UUID,
    invoice_id: uuid.UUID,
    reason: str,
    created_by: uuid.UUID,
    clock: Clock,
    order_repo: WorkOrderRepository,
    profile_repo: FiscalProfileRepository,
    range_repo: CaiRangeRepository,
    invoice_repo: FiscalInvoiceRepository,
    credit_note_repo: CreditNoteRepository,
) -> tuple[FiscalCreditNote, bool]:
    """Issue a full-amount Nota de Credito against an issued Factura, or
    replay an idempotent issuance (AD-13): normalize the reason, lock
    the order, replay, lock the Factura, lock the profile, select and
    allocate from the usable `06` range, build and insert the
    snapshot, then stamp the Factura's `credited_at` -- the only
    update its own AD-10 trigger allows.

    The lock order extends AD-5: the order row, then the Factura, then
    the fiscal profile, then the range. A replayed credit note returns
    before any of the later checks and never consumes a number.

    Returns ``(credit_note, is_new)``: ``is_new`` is False when
    ``credit_note_id`` already existed with identical fields (the
    caller should respond 200, not 201).

    Raises:
        InvalidCreditNoteReason: ``reason`` is empty after trimming,
            or exceeds 300 characters.
        FiscalInvoiceNotFound: no such Factura in this workshop.
        CreditNoteIdConflict: ``credit_note_id`` already exists with
            fields that do not match this request.
        InvoiceAlreadyCredited: the Factura already has a credit note.
        FiscalProfileMissing: the workshop has no fiscal profile.
        CaiRangeMissing / CaiRangeExpired / CaiRangeExhausted: no `06`
            range is usable today (AD-4, AD-13).
    """
    normalized_reason = _normalize_credit_note_reason(reason)

    invoice = invoice_repo.get_by_id(workshop_id=workshop_id, invoice_id=invoice_id)
    if invoice is None:
        raise FiscalInvoiceNotFound(invoice_id)

    # Locks the same row every line edit and the original issuance lock,
    # so a credit note is always serialized against both (AD-5).
    order_repo.get_for_update(workshop_id=workshop_id, order_id=invoice.order_id)

    existing = credit_note_repo.get_by_id(workshop_id=workshop_id, credit_note_id=credit_note_id)
    if existing is not None:
        if not _credit_note_fields_match(existing, invoice_id=invoice_id, reason=normalized_reason):
            raise CreditNoteIdConflict(credit_note_id)
        return existing, False

    # Re-read the Factura under its own lock: the unlocked read above
    # can already be stale, and this is the row whose `credited_at`
    # decides eligibility and whose own lock serializes two concurrent
    # credit notes against it.
    invoice = invoice_repo.get_for_update(workshop_id=workshop_id, invoice_id=invoice_id)
    if invoice is None:
        raise FiscalInvoiceNotFound(invoice_id)
    if invoice.credited_at is not None:
        raise InvoiceAlreadyCredited(invoice_id)

    profile = profile_repo.get_for_update(workshop_id=workshop_id)
    if profile is None:
        raise FiscalProfileMissing()

    now = clock.now()
    today = now.astimezone(HONDURAS_TZ).date()
    ranges = range_repo.list(workshop_id=workshop_id, document_type=DocumentType.credit_note)
    cai_range = select_range(ranges, today)

    correlative = range_repo.allocate(range_id=cai_range.id, now=now)
    if correlative is None:
        # The profile lock serializes every fiscal write for this
        # workshop, so this should never actually happen -- but fail
        # safely as exhausted rather than crash if it somehow does.
        raise CaiRangeExhausted()

    number = DocumentNumber(
        establishment=profile.establishment_code,
        emission_point=profile.emission_point_code,
        document_type=DocumentType.credit_note,
        correlative=correlative,
    )

    credit_note = FiscalCreditNote(
        id=credit_note_id,
        workshop_id=workshop_id,
        invoice_id=invoice_id,
        order_id=invoice.order_id,
        cai_range_id=cai_range.id,
        correlative=correlative,
        number=str(number),
        issued_at=now,
        issue_date=today,
        issuer_rtn=profile.rtn,
        issuer_legal_name=profile.legal_name,
        issuer_trade_name=profile.trade_name,
        issuer_address=profile.address,
        issuer_phone=profile.phone,
        issuer_email=profile.email,
        cai=cai_range.cai,
        range_first_number=str(
            DocumentNumber(
                establishment=cai_range.establishment_code,
                emission_point=cai_range.emission_point_code,
                document_type=cai_range.document_type,
                correlative=cai_range.range_start,
            )
        ),
        range_last_number=str(
            DocumentNumber(
                establishment=cai_range.establishment_code,
                emission_point=cai_range.emission_point_code,
                document_type=cai_range.document_type,
                correlative=cai_range.range_end,
            )
        ),
        issue_deadline=cai_range.issue_deadline,
        buyer_name=invoice.buyer_name,
        buyer_rtn=invoice.buyer_rtn,
        original_cai=invoice.cai,
        original_number=invoice.number,
        original_issue_date=invoice.issue_date,
        reason=normalized_reason,
        taxable_15_cents=invoice.taxable_15_cents,
        isv_15_cents=invoice.isv_15_cents,
        total_cents=invoice.total_cents,
        total_in_words=invoice.total_in_words,
        created_by=created_by,
        created_at=now,
    )
    credit_note_repo.add(credit_note)
    invoice_repo.mark_credited(invoice_id=invoice_id, credited_at=now)
    return credit_note, True


def get_credit_note(
    *, workshop_id: uuid.UUID, credit_note_id: uuid.UUID, credit_note_repo: CreditNoteRepository
) -> FiscalCreditNote:
    """Raises: CreditNoteNotFound: no such credit note in this workshop."""
    credit_note = credit_note_repo.get_by_id(workshop_id=workshop_id, credit_note_id=credit_note_id)
    if credit_note is None:
        raise CreditNoteNotFound(credit_note_id)
    return credit_note

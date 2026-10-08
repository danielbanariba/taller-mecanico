"""FastAPI router for the invoicing feature."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from taller.customers.domain.errors import InvalidRtn
from taller.identity.adapters.dependencies import (
    get_clock,
    get_current_user,
    get_current_workshop_id,
)
from taller.identity.application.ports import Clock
from taller.identity.domain.entities import User
from taller.identity.domain.errors import InvalidPhoneNumber
from taller.invoicing.adapters.repositories import (
    SqlAlchemyCaiRangeRepository,
    SqlAlchemyCreditNoteRepository,
    SqlAlchemyFiscalInvoiceRepository,
    SqlAlchemyFiscalProfileRepository,
)
from taller.invoicing.adapters.schemas import (
    CaiRangeCreateRequest,
    CaiRangeOut,
    CaiRangePatchRequest,
    FiscalCreditNoteCreateRequest,
    FiscalCreditNoteOut,
    FiscalInvoiceCreateRequest,
    FiscalInvoiceOut,
    FiscalInvoiceSummaryOut,
    FiscalProfileOut,
    FiscalProfileSaveRequest,
    InvoicingSettingsOut,
)
from taller.invoicing.application.use_cases import (
    create_range,
    get_credit_note,
    get_invoice,
    get_settings,
    issue_credit_note,
    issue_invoice,
    list_order_invoices,
    save_profile,
    update_range,
)
from taller.invoicing.domain.errors import (
    BuyerIdentificationRequired,
    BuyerNameRequired,
    CaiDeadlinePassed,
    CaiDeadlineTooFar,
    CaiRangeExhausted,
    CaiRangeExpired,
    CaiRangeIdConflict,
    CaiRangeImmutable,
    CaiRangeMissing,
    CaiRangeNotFound,
    CaiRangeOverlap,
    CreditNoteIdConflict,
    CreditNoteNotFound,
    FiscalInvoiceIdConflict,
    FiscalInvoiceNotFound,
    FiscalProfileCodesLocked,
    FiscalProfileMissing,
    InvalidCai,
    InvalidCaiRange,
    InvalidCreditNoteReason,
    InvalidEmail,
    InvalidEmissionPointCode,
    InvalidEstablishmentCode,
    InvoiceAlreadyCredited,
    InvoiceAmountTooLarge,
    InvoiceAmountZero,
    UnsupportedDocumentType,
    WorkOrderAlreadyInvoiced,
    WorkOrderNotInvoiceable,
)
from taller.invoicing.domain.ranges import range_states
from taller.shared.db import get_db
from taller.shared.timezone import local_today
from taller.workorders.adapters.repositories import SqlAlchemyWorkOrderRepository
from taller.workorders.domain.errors import WorkOrderNotFound

invoicing_router = APIRouter(prefix="/invoicing", tags=["invoicing"])

#: `fiscal_invoices`'s primary key constraint name, as Postgres reports it on
#: an `IntegrityError` (AD-6's retry-once rule).
_INVOICE_PK_CONSTRAINT = "fiscal_invoices_pkey"

#: `fiscal_credit_notes`'s primary key constraint name (AD-13's retry-once
#: rule, mirroring `_INVOICE_PK_CONSTRAINT`).
_CREDIT_NOTE_PK_CONSTRAINT = "fiscal_credit_notes_pkey"


def _violated_constraint(exc: IntegrityError) -> str | None:
    """Mirrors `taller.workorders.adapters.router._violated_constraint`."""
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


def _range_out(
    cai_range, *, workshop_id: uuid.UUID, clock: Clock, range_repo: SqlAlchemyCaiRangeRepository
) -> CaiRangeOut:
    """Recompute the just-written range's derived state (AD-4) against
    every sibling of its type, so the response always matches what a
    following `GET /invoicing/settings` would report.
    """
    siblings = range_repo.list(workshop_id=workshop_id, document_type=cai_range.document_type)
    state = range_states(siblings, local_today(clock))[cai_range.id]
    return CaiRangeOut.from_domain(cai_range, state=state)


@invoicing_router.put("/profile", response_model=FiscalProfileOut)
def save_profile_route(
    payload: FiscalProfileSaveRequest,
    response: Response,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    clock: Clock = Depends(get_clock),
    db: Session = Depends(get_db),
) -> FiscalProfileOut:
    profile_repo = SqlAlchemyFiscalProfileRepository(db)
    range_repo = SqlAlchemyCaiRangeRepository(db)
    try:
        profile, is_new = save_profile(
            workshop_id=workshop_id,
            rtn=payload.rtn,
            legal_name=payload.legal_name,
            trade_name=payload.trade_name,
            address=payload.address,
            phone=payload.phone,
            email=payload.email,
            establishment_code=payload.establishment_code,
            emission_point_code=payload.emission_point_code,
            clock=clock,
            profile_repo=profile_repo,
            range_repo=range_repo,
        )
        db.commit()
    except InvalidRtn as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_rtn") from exc
    except InvalidPhoneNumber as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_phone") from exc
    except InvalidEmail as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_email") from exc
    except InvalidEstablishmentCode as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_establishment_code"
        ) from exc
    except InvalidEmissionPointCode as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_emission_point_code"
        ) from exc
    except FiscalProfileCodesLocked as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="fiscal_profile_codes_locked") from exc

    response.status_code = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
    return FiscalProfileOut.from_domain(profile)


@invoicing_router.get("/settings", response_model=InvoicingSettingsOut)
def get_settings_route(
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    clock: Clock = Depends(get_clock),
    db: Session = Depends(get_db),
) -> InvoicingSettingsOut:
    profile_repo = SqlAlchemyFiscalProfileRepository(db)
    range_repo = SqlAlchemyCaiRangeRepository(db)
    settings = get_settings(
        workshop_id=workshop_id, clock=clock, profile_repo=profile_repo, range_repo=range_repo
    )
    return InvoicingSettingsOut.from_domain(settings)


@invoicing_router.post(
    "/cai-ranges", response_model=CaiRangeOut, status_code=status.HTTP_201_CREATED
)
def create_range_route(
    payload: CaiRangeCreateRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    clock: Clock = Depends(get_clock),
    db: Session = Depends(get_db),
) -> CaiRangeOut:
    profile_repo = SqlAlchemyFiscalProfileRepository(db)
    range_repo = SqlAlchemyCaiRangeRepository(db)
    try:
        cai_range, is_new = create_range(
            workshop_id=workshop_id,
            range_id=payload.id,
            document_type=payload.document_type,
            cai=payload.cai,
            range_start=payload.range_start,
            range_end=payload.range_end,
            issue_deadline=payload.issue_deadline,
            created_by=current_user.id,
            clock=clock,
            profile_repo=profile_repo,
            range_repo=range_repo,
        )
        db.commit()
    except UnsupportedDocumentType as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="unsupported_document_type"
        ) from exc
    except InvalidCai as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_cai") from exc
    except InvalidCaiRange as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_cai_range"
        ) from exc
    except CaiDeadlinePassed as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="cai_deadline_passed"
        ) from exc
    except CaiDeadlineTooFar as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="cai_deadline_too_far"
        ) from exc
    except FiscalProfileMissing as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="fiscal_profile_missing") from exc
    except CaiRangeIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_id_conflict") from exc
    except CaiRangeOverlap as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_overlap") from exc

    if not is_new:
        response.status_code = status.HTTP_200_OK
    return _range_out(cai_range, workshop_id=workshop_id, clock=clock, range_repo=range_repo)


@invoicing_router.patch("/cai-ranges/{range_id}", response_model=CaiRangeOut)
def update_range_route(
    range_id: uuid.UUID,
    payload: CaiRangePatchRequest,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    clock: Clock = Depends(get_clock),
    db: Session = Depends(get_db),
) -> CaiRangeOut:
    profile_repo = SqlAlchemyFiscalProfileRepository(db)
    range_repo = SqlAlchemyCaiRangeRepository(db)
    fields = payload.model_dump(exclude_unset=True)
    try:
        cai_range = update_range(
            workshop_id=workshop_id,
            range_id=range_id,
            fields=fields,
            clock=clock,
            profile_repo=profile_repo,
            range_repo=range_repo,
        )
        db.commit()
    except FiscalProfileMissing as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="fiscal_profile_missing") from exc
    except CaiRangeNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="cai_range_not_found") from exc
    except CaiRangeImmutable as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_immutable") from exc
    except UnsupportedDocumentType as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="unsupported_document_type"
        ) from exc
    except InvalidCai as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_cai") from exc
    except InvalidCaiRange as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_cai_range"
        ) from exc
    except CaiDeadlinePassed as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="cai_deadline_passed"
        ) from exc
    except CaiDeadlineTooFar as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="cai_deadline_too_far"
        ) from exc
    except CaiRangeOverlap as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_overlap") from exc

    return _range_out(cai_range, workshop_id=workshop_id, clock=clock, range_repo=range_repo)


@invoicing_router.post(
    "/invoices", response_model=FiscalInvoiceOut, status_code=status.HTTP_201_CREATED
)
def issue_invoice_route(
    payload: FiscalInvoiceCreateRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    clock: Clock = Depends(get_clock),
    db: Session = Depends(get_db),
) -> FiscalInvoiceOut:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    profile_repo = SqlAlchemyFiscalProfileRepository(db)
    range_repo = SqlAlchemyCaiRangeRepository(db)
    invoice_repo = SqlAlchemyFiscalInvoiceRepository(db)
    credit_note_repo = SqlAlchemyCreditNoteRepository(db)

    def _attempt() -> tuple:
        result = issue_invoice(
            workshop_id=workshop_id,
            invoice_id=payload.id,
            order_id=payload.order_id,
            buyer_name=payload.buyer_name,
            buyer_rtn=payload.buyer_rtn,
            created_by=current_user.id,
            clock=clock,
            order_repo=order_repo,
            profile_repo=profile_repo,
            range_repo=range_repo,
            invoice_repo=invoice_repo,
        )
        db.commit()
        return result

    try:
        invoice, is_new = _attempt()
    except InvalidRtn as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_rtn") from exc
    except BuyerNameRequired as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="buyer_name_required"
        ) from exc
    except WorkOrderNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_not_found") from exc
    except FiscalInvoiceIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="fiscal_invoice_id_conflict") from exc
    except WorkOrderNotInvoiceable as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="work_order_not_invoiceable") from exc
    except WorkOrderAlreadyInvoiced as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="work_order_already_invoiced") from exc
    except InvoiceAmountZero as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="invoice_amount_zero") from exc
    except InvoiceAmountTooLarge as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="invoice_amount_too_large") from exc
    except BuyerIdentificationRequired as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="buyer_identification_required"
        ) from exc
    except (FiscalProfileMissing, CaiRangeMissing) as exc:
        # Both configuration gaps share one code at issuance (the
        # `fiscal-invoices` spec's "invoicing_not_configured"): the web
        # never needs to tell a missing profile apart from a missing
        # range. An existing-but-exhausted-or-expired range keeps its
        # own direct code instead, per the `cai-ranges` spec.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="invoicing_not_configured") from exc
    except CaiRangeExpired as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_expired") from exc
    except CaiRangeExhausted as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_exhausted") from exc
    except IntegrityError as first_exc:
        db.rollback()
        # Another request committed the same invoice id between our
        # replay check and our insert (AD-6): retry once so the replay
        # check resolves it cleanly instead of crashing. The rollback
        # above also undoes this attempt's correlative allocation, so
        # the retry never skips a number.
        if _violated_constraint(first_exc) != _INVOICE_PK_CONSTRAINT:
            raise
        try:
            invoice, is_new = _attempt()
        except InvalidRtn as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_rtn"
            ) from exc
        except BuyerNameRequired as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail="buyer_name_required"
            ) from exc
        except WorkOrderNotFound as exc:
            db.rollback()
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_not_found") from exc
        except FiscalInvoiceIdConflict as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="fiscal_invoice_id_conflict"
            ) from exc
        except WorkOrderNotInvoiceable as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="work_order_not_invoiceable"
            ) from exc
        except WorkOrderAlreadyInvoiced as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="work_order_already_invoiced"
            ) from exc
        except InvoiceAmountZero as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, detail="invoice_amount_zero") from exc
        except InvoiceAmountTooLarge as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="invoice_amount_too_large"
            ) from exc
        except BuyerIdentificationRequired as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail="buyer_identification_required"
            ) from exc
        except (FiscalProfileMissing, CaiRangeMissing) as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="invoicing_not_configured"
            ) from exc
        except CaiRangeExpired as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_expired") from exc
        except CaiRangeExhausted as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_exhausted") from exc
        except IntegrityError as exc:
            db.rollback()
            if _violated_constraint(exc) == _INVOICE_PK_CONSTRAINT:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, detail="fiscal_invoice_id_conflict"
                ) from exc
            raise

    if not is_new:
        response.status_code = status.HTTP_200_OK
    credit_note = credit_note_repo.get_for_invoice(workshop_id=workshop_id, invoice_id=invoice.id)
    return FiscalInvoiceOut.from_domain(invoice, credit_note=credit_note)


@invoicing_router.get("/invoices/{invoice_id}", response_model=FiscalInvoiceOut)
def get_invoice_route(
    invoice_id: uuid.UUID,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> FiscalInvoiceOut:
    invoice_repo = SqlAlchemyFiscalInvoiceRepository(db)
    credit_note_repo = SqlAlchemyCreditNoteRepository(db)
    try:
        invoice = get_invoice(
            workshop_id=workshop_id, invoice_id=invoice_id, invoice_repo=invoice_repo
        )
    except FiscalInvoiceNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="fiscal_invoice_not_found") from exc
    credit_note = credit_note_repo.get_for_invoice(workshop_id=workshop_id, invoice_id=invoice.id)
    return FiscalInvoiceOut.from_domain(invoice, credit_note=credit_note)


@invoicing_router.get("/invoices", response_model=list[FiscalInvoiceSummaryOut])
def list_invoices_route(
    order_id: uuid.UUID = Query(),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> list[FiscalInvoiceSummaryOut]:
    invoice_repo = SqlAlchemyFiscalInvoiceRepository(db)
    credit_note_repo = SqlAlchemyCreditNoteRepository(db)
    invoices = list_order_invoices(
        workshop_id=workshop_id, order_id=order_id, invoice_repo=invoice_repo
    )
    return [
        FiscalInvoiceSummaryOut.from_domain(
            invoice,
            credit_note=credit_note_repo.get_for_invoice(
                workshop_id=workshop_id, invoice_id=invoice.id
            ),
        )
        for invoice in invoices
    ]


@invoicing_router.post(
    "/credit-notes", response_model=FiscalCreditNoteOut, status_code=status.HTTP_201_CREATED
)
def issue_credit_note_route(
    payload: FiscalCreditNoteCreateRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    clock: Clock = Depends(get_clock),
    db: Session = Depends(get_db),
) -> FiscalCreditNoteOut:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    profile_repo = SqlAlchemyFiscalProfileRepository(db)
    range_repo = SqlAlchemyCaiRangeRepository(db)
    invoice_repo = SqlAlchemyFiscalInvoiceRepository(db)
    credit_note_repo = SqlAlchemyCreditNoteRepository(db)

    def _attempt() -> tuple:
        result = issue_credit_note(
            workshop_id=workshop_id,
            credit_note_id=payload.id,
            invoice_id=payload.invoice_id,
            reason=payload.reason,
            created_by=current_user.id,
            clock=clock,
            order_repo=order_repo,
            profile_repo=profile_repo,
            range_repo=range_repo,
            invoice_repo=invoice_repo,
            credit_note_repo=credit_note_repo,
        )
        db.commit()
        return result

    try:
        credit_note, is_new = _attempt()
    except InvalidCreditNoteReason as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_credit_note_reason"
        ) from exc
    except FiscalInvoiceNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="invoice_not_found") from exc
    except CreditNoteIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="credit_note_id_conflict") from exc
    except InvoiceAlreadyCredited as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="credit_note_already_issued") from exc
    except (FiscalProfileMissing, CaiRangeMissing) as exc:
        # Both configuration gaps share one code (mirrors
        # `issue_invoice_route`'s `invoicing_not_configured`): the web
        # never needs to tell a missing profile apart from a missing
        # `06` range. An existing-but-exhausted-or-expired range keeps
        # its own direct code instead, per the `cai-ranges` spec.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="invoicing_not_configured") from exc
    except CaiRangeExpired as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_expired") from exc
    except CaiRangeExhausted as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_exhausted") from exc
    except IntegrityError as first_exc:
        db.rollback()
        # Mirrors `issue_invoice_route`'s retry-once dance: a credit note
        # id reused against a *different* invoice races on the primary
        # key with no shared lock serializing the two attempts (they
        # lock different orders). The rollback above also undoes this
        # attempt's allocated correlative, so the retry's replay check
        # resolves it cleanly instead of burning a number.
        if _violated_constraint(first_exc) != _CREDIT_NOTE_PK_CONSTRAINT:
            raise
        try:
            credit_note, is_new = _attempt()
        except InvalidCreditNoteReason as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_credit_note_reason"
            ) from exc
        except FiscalInvoiceNotFound as exc:
            db.rollback()
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="invoice_not_found") from exc
        except CreditNoteIdConflict as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, detail="credit_note_id_conflict") from exc
        except InvoiceAlreadyCredited as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="credit_note_already_issued"
            ) from exc
        except (FiscalProfileMissing, CaiRangeMissing) as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="invoicing_not_configured"
            ) from exc
        except CaiRangeExpired as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_expired") from exc
        except CaiRangeExhausted as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, detail="cai_range_exhausted") from exc
        except IntegrityError as exc:
            db.rollback()
            if _violated_constraint(exc) == _CREDIT_NOTE_PK_CONSTRAINT:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, detail="credit_note_id_conflict"
                ) from exc
            raise

    if not is_new:
        response.status_code = status.HTTP_200_OK
    return FiscalCreditNoteOut.from_domain(credit_note)


@invoicing_router.get("/credit-notes/{credit_note_id}", response_model=FiscalCreditNoteOut)
def get_credit_note_route(
    credit_note_id: uuid.UUID,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> FiscalCreditNoteOut:
    credit_note_repo = SqlAlchemyCreditNoteRepository(db)
    try:
        credit_note = get_credit_note(
            workshop_id=workshop_id,
            credit_note_id=credit_note_id,
            credit_note_repo=credit_note_repo,
        )
    except CreditNoteNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="credit_note_not_found") from exc
    return FiscalCreditNoteOut.from_domain(credit_note)

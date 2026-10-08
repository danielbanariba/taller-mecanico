"""FastAPI router for the invoicing feature."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
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
    SqlAlchemyFiscalProfileRepository,
)
from taller.invoicing.adapters.schemas import (
    CaiRangeCreateRequest,
    CaiRangeOut,
    CaiRangePatchRequest,
    FiscalProfileOut,
    FiscalProfileSaveRequest,
    InvoicingSettingsOut,
)
from taller.invoicing.application.use_cases import (
    create_range,
    get_settings,
    save_profile,
    update_range,
)
from taller.invoicing.domain.errors import (
    CaiDeadlinePassed,
    CaiDeadlineTooFar,
    CaiRangeIdConflict,
    CaiRangeImmutable,
    CaiRangeNotFound,
    CaiRangeOverlap,
    FiscalProfileCodesLocked,
    FiscalProfileMissing,
    InvalidCai,
    InvalidCaiRange,
    InvalidEmail,
    InvalidEmissionPointCode,
    InvalidEstablishmentCode,
    UnsupportedDocumentType,
)
from taller.invoicing.domain.ranges import range_states
from taller.shared.db import get_db
from taller.shared.timezone import local_today

invoicing_router = APIRouter(prefix="/invoicing", tags=["invoicing"])


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

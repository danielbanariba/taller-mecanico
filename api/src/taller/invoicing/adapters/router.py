"""FastAPI router for the invoicing feature."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from taller.customers.domain.errors import InvalidRtn
from taller.identity.adapters.dependencies import get_clock, get_current_workshop_id
from taller.identity.application.ports import Clock
from taller.identity.domain.errors import InvalidPhoneNumber
from taller.invoicing.adapters.repositories import (
    SqlAlchemyCaiRangeRepository,
    SqlAlchemyFiscalProfileRepository,
)
from taller.invoicing.adapters.schemas import (
    FiscalProfileOut,
    FiscalProfileSaveRequest,
    InvoicingSettingsOut,
)
from taller.invoicing.application.use_cases import get_settings, save_profile
from taller.invoicing.domain.errors import (
    FiscalProfileCodesLocked,
    InvalidEmail,
    InvalidEmissionPointCode,
    InvalidEstablishmentCode,
)
from taller.shared.db import get_db

invoicing_router = APIRouter(prefix="/invoicing", tags=["invoicing"])


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

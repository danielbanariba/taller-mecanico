"""HTTP routes for registration, login, logout, and the current session."""

import math

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from taller.identity.adapters.dependencies import (
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_PATH,
    get_clock,
    get_current_user,
    get_password_hasher,
    get_token_service,
)
from taller.identity.adapters.repositories import (
    SqlAlchemyLoginThrottleRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyWorkshopRepository,
)
from taller.identity.adapters.schemas import LoginRequest, MeResponse, RegisterRequest
from taller.identity.adapters.token_service import SESSION_MAX_AGE, JwtTokenService
from taller.identity.application.ports import Clock, PasswordHasher
from taller.identity.application.use_cases import attempt_login, register_workshop
from taller.identity.domain.entities import User
from taller.identity.domain.errors import (
    InvalidCredentials,
    PhoneAlreadyRegistered,
    TooManyLoginAttempts,
)
from taller.shared.config import Settings, get_settings
from taller.shared.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

PHONE_UNIQUE_INDEX = "ix_users_phone"


def _violated_constraint(exc: IntegrityError) -> str | None:
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


def _set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(SESSION_MAX_AGE.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path=SESSION_COOKIE_PATH,
    )


@router.post("/register", response_model=MeResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    hasher: PasswordHasher = Depends(get_password_hasher),
    token_service: JwtTokenService = Depends(get_token_service),
) -> MeResponse:
    user_repo = SqlAlchemyUserRepository(db)
    workshop_repo = SqlAlchemyWorkshopRepository(db)
    try:
        workshop, user = register_workshop(
            workshop_name=payload.workshop_name,
            owner_name=payload.owner_name,
            phone_raw=payload.phone,
            password=payload.password,
            user_repo=user_repo,
            workshop_repo=workshop_repo,
            hasher=hasher,
        )
        db.commit()
    except PhoneAlreadyRegistered as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="phone_already_registered") from exc
    except IntegrityError as exc:
        # Defends against the race between the pre-check above and the
        # insert (two concurrent registrations for the same phone); the
        # unique index on users.phone is the real guarantee. Any other
        # integrity error is a bug and must not be reported as a duplicate.
        db.rollback()
        if _violated_constraint(exc) != PHONE_UNIQUE_INDEX:
            raise
        raise HTTPException(status.HTTP_409_CONFLICT, detail="phone_already_registered") from exc

    token = token_service.issue(user_id=user.id, workshop_id=workshop.id)
    _set_session_cookie(response, token, settings)
    return MeResponse.from_domain(user, workshop)


@router.post("/login", response_model=MeResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    hasher: PasswordHasher = Depends(get_password_hasher),
    token_service: JwtTokenService = Depends(get_token_service),
    clock: Clock = Depends(get_clock),
) -> MeResponse:
    user_repo = SqlAlchemyUserRepository(db)
    try:
        user = attempt_login(
            phone_raw=payload.phone,
            password=payload.password,
            user_repo=user_repo,
            hasher=hasher,
            throttle_repo=SqlAlchemyLoginThrottleRepository(db),
            clock=clock,
        )
    except TooManyLoginAttempts as exc:
        db.rollback()
        retry_after = max(1, math.ceil(exc.retry_after.total_seconds()))
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too_many_login_attempts",
            headers={"Retry-After": str(retry_after)},
        ) from exc
    except InvalidCredentials as exc:
        # Commit the counted failure: `get_db` never commits, so without
        # this the failed attempt would roll back with the 401 response and
        # the lockout would never trigger.
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials") from exc

    workshop_repo = SqlAlchemyWorkshopRepository(db)
    workshop = workshop_repo.get_by_id(user.workshop_id)
    if workshop is None:
        # Data-integrity invariant: every user's workshop_id is a not-null
        # foreign key to an existing workshop that is never deleted.
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="workshop_not_found")

    # Persists the reset of earlier failed attempts.
    db.commit()
    token = token_service.issue(user_id=user.id, workshop_id=workshop.id)
    _set_session_cookie(response, token, settings)
    return MeResponse.from_domain(user, workshop)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, settings: Settings = Depends(get_settings)) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path=SESSION_COOKIE_PATH,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MeResponse:
    workshop_repo = SqlAlchemyWorkshopRepository(db)
    workshop = workshop_repo.get_by_id(current_user.workshop_id)
    if workshop is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")
    return MeResponse.from_domain(current_user, workshop)

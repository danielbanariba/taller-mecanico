"""FastAPI dependencies for the identity feature.

``get_current_user`` and ``get_current_workshop_id`` are the dependencies
every other feature should depend on to scope its own queries to the
authenticated workshop (tenant isolation).
"""

import uuid
from functools import lru_cache

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from taller.identity.adapters.clock import SystemClock
from taller.identity.adapters.password_hasher import PwdlibPasswordHasher
from taller.identity.adapters.repositories import SqlAlchemyUserRepository
from taller.identity.adapters.token_service import JwtTokenService
from taller.identity.application.ports import Clock, PasswordHasher
from taller.identity.application.use_cases import get_current_user as _resolve_current_user
from taller.identity.domain.entities import User
from taller.identity.domain.errors import NotAuthenticated
from taller.shared.config import Settings, get_settings
from taller.shared.db import get_db

#: Name of the cookie that carries the signed session token.
SESSION_COOKIE_NAME = "taller_session"

#: Cookie path: the web app and the API are served same-origin, and the
#: cookie is only ever needed for API requests.
SESSION_COOKIE_PATH = "/api"


@lru_cache
def get_password_hasher() -> PasswordHasher:
    """Return the process-wide password hasher instance."""
    return PwdlibPasswordHasher()


def get_clock() -> Clock:
    """The clock login throttling reads; tests override it to move time."""
    return SystemClock()


def get_token_service(settings: Settings = Depends(get_settings)) -> JwtTokenService:
    return JwtTokenService(secret=settings.jwt_secret)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token_service: JwtTokenService = Depends(get_token_service),
) -> User:
    """Resolve the authenticated user from the session cookie, or 401."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")

    user_repo = SqlAlchemyUserRepository(db)
    try:
        return _resolve_current_user(token=token, token_service=token_service, user_repo=user_repo)
    except NotAuthenticated as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="not_authenticated") from exc


def get_current_workshop_id(user: User = Depends(get_current_user)) -> uuid.UUID:
    """The authenticated user's workshop id, for scoping tenant queries."""
    return user.workshop_id

"""JWT (HS256) session token issuing and verification, via PyJWT."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt

from taller.identity.application.ports import SessionTokenPayload
from taller.identity.domain.errors import NotAuthenticated

#: How long a session cookie (and the JWT inside it) stays valid for.
SESSION_MAX_AGE = timedelta(days=30)

_ALGORITHM = "HS256"


class JwtTokenService:
    """Signs and verifies session tokens carrying the user and workshop id."""

    def __init__(self, secret: str) -> None:
        self._secret = secret

    def issue(self, *, user_id: uuid.UUID, workshop_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "wid": str(workshop_id),
            "iat": now,
            "exp": now + SESSION_MAX_AGE,
        }
        return jwt.encode(payload, self._secret, algorithm=_ALGORITHM)

    def verify(self, token: str) -> SessionTokenPayload:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[_ALGORITHM])
            return SessionTokenPayload(
                user_id=uuid.UUID(payload["sub"]),
                workshop_id=uuid.UUID(payload["wid"]),
            )
        except (jwt.PyJWTError, KeyError, ValueError) as exc:
            raise NotAuthenticated from exc

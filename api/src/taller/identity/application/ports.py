"""Ports the identity use cases depend on, implemented by adapters."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from taller.identity.domain.entities import User, Workshop
from taller.identity.domain.login_throttle import LoginThrottle
from taller.identity.domain.phone_number import PhoneNumber


class UserRepository(Protocol):
    def get_by_phone(self, phone: PhoneNumber) -> User | None: ...

    def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    def add(self, user: User) -> None: ...


class WorkshopRepository(Protocol):
    def get_by_id(self, workshop_id: uuid.UUID) -> Workshop | None: ...

    def add(self, workshop: Workshop) -> None: ...


class LoginThrottleRepository(Protocol):
    def get_for_update(self, phone: PhoneNumber) -> LoginThrottle:
        """Return the phone's throttle state, locked until the transaction ends.

        A phone with no state yet gets a fresh, zero-failure one, so even
        its first login attempt is serialized against concurrent ones and
        no failed attempt can be lost to a race.
        """
        ...

    def save(self, throttle: LoginThrottle) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime:
        """The current time, timezone-aware (UTC)."""
        ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


@dataclass(frozen=True, slots=True)
class SessionTokenPayload:
    """The identity a verified session token carries."""

    user_id: uuid.UUID
    workshop_id: uuid.UUID


class TokenService(Protocol):
    def issue(self, *, user_id: uuid.UUID, workshop_id: uuid.UUID) -> str: ...

    def verify(self, token: str) -> SessionTokenPayload:
        """Return the token's payload.

        Raises:
            taller.identity.domain.errors.NotAuthenticated: the token is
            missing, malformed, tampered, or expired.
        """
        ...

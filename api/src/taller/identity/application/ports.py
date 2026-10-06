"""Ports the identity use cases depend on, implemented by adapters."""

import uuid
from dataclasses import dataclass
from typing import Protocol

from taller.identity.domain.entities import User, Workshop
from taller.identity.domain.phone_number import PhoneNumber


class UserRepository(Protocol):
    def get_by_phone(self, phone: PhoneNumber) -> User | None: ...

    def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    def add(self, user: User) -> None: ...


class WorkshopRepository(Protocol):
    def get_by_id(self, workshop_id: uuid.UUID) -> Workshop | None: ...

    def add(self, workshop: Workshop) -> None: ...


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

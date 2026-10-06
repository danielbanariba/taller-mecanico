"""Use cases for the identity feature: registration, login, session resolution."""

import uuid
from datetime import UTC, datetime

from taller.identity.application.ports import (
    PasswordHasher,
    TokenService,
    UserRepository,
    WorkshopRepository,
)
from taller.identity.domain.entities import User, Workshop
from taller.identity.domain.errors import (
    InvalidCredentials,
    NotAuthenticated,
    PhoneAlreadyRegistered,
)
from taller.identity.domain.phone_number import PhoneNumber

# A fixed password, hashed lazily on first use with whichever hasher the
# caller passes in. An authentication attempt for an unknown phone number
# still pays the cost of a real Argon2 verification against this hash, so a
# timing difference between "unknown phone" (would otherwise return
# instantly) and "wrong password" (one real hash verification) can't be used
# to enumerate which phone numbers are registered.
_dummy_password_hash: str | None = None


def _dummy_hash(hasher: PasswordHasher) -> str:
    global _dummy_password_hash
    if _dummy_password_hash is None:
        _dummy_password_hash = hasher.hash("dummy-password-for-constant-time-comparison")
    return _dummy_password_hash


def register_workshop(
    *,
    workshop_name: str,
    owner_name: str,
    phone_raw: str,
    password: str,
    user_repo: UserRepository,
    workshop_repo: WorkshopRepository,
    hasher: PasswordHasher,
) -> tuple[Workshop, User]:
    """Register a new workshop together with its owner account.

    Raises:
        taller.identity.domain.errors.InvalidPhoneNumber: the phone cannot
            be normalized.
        PhoneAlreadyRegistered: another user already owns that phone number.
    """
    phone = PhoneNumber.from_raw(phone_raw)
    if user_repo.get_by_phone(phone) is not None:
        raise PhoneAlreadyRegistered(phone.value)

    now = datetime.now(UTC)
    workshop = Workshop(id=uuid.uuid4(), name=workshop_name, created_at=now)
    workshop_repo.add(workshop)

    user = User(
        id=uuid.uuid4(),
        workshop_id=workshop.id,
        full_name=owner_name,
        phone=phone,
        password_hash=hasher.hash(password),
        role="owner",
        created_at=now,
    )
    user_repo.add(user)
    return workshop, user


def authenticate(
    *,
    phone_raw: str,
    password: str,
    user_repo: UserRepository,
    hasher: PasswordHasher,
) -> User:
    """Verify a phone/password pair and return the matching user.

    Both an unknown phone and a wrong password raise the identical
    ``InvalidCredentials`` error, and both pay the cost of one real hash
    verification, so a caller (or an attacker timing responses) cannot tell
    the two cases apart.
    """
    phone = PhoneNumber.from_raw(phone_raw)
    user = user_repo.get_by_phone(phone)
    if user is None:
        hasher.verify(password, _dummy_hash(hasher))
        raise InvalidCredentials
    if not hasher.verify(password, user.password_hash):
        raise InvalidCredentials
    return user


def get_current_user(
    *,
    token: str,
    token_service: TokenService,
    user_repo: UserRepository,
) -> User:
    """Resolve the user a signed session token identifies.

    Raises:
        NotAuthenticated: the token is missing, malformed, tampered,
            expired, or no longer identifies an existing user.
    """
    payload = token_service.verify(token)
    user = user_repo.get_by_id(payload.user_id)
    if user is None or user.workshop_id != payload.workshop_id:
        raise NotAuthenticated
    return user

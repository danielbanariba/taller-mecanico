"""Domain entities for the identity feature: workshops (tenants) and users."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from taller.identity.domain.phone_number import PhoneNumber


@dataclass(slots=True)
class Workshop:
    """A repair shop: the tenant that every other record is scoped to."""

    id: uuid.UUID
    name: str
    created_at: datetime


@dataclass(slots=True)
class User:
    """A workshop user. Only the ``owner`` role exists for now."""

    id: uuid.UUID
    workshop_id: uuid.UUID
    full_name: str
    phone: PhoneNumber
    password_hash: str
    role: str
    created_at: datetime

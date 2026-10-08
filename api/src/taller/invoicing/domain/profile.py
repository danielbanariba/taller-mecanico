"""The fiscal profile domain entity (AD-3): one per workshop, holding
every Art. 10-11 issuer field. ``PUT /invoicing/profile`` requires
every field, so a saved profile is always complete; `is_complete` is
the one predicate `get_settings` and issuance both read, so they can
never disagree about readiness.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from taller.invoicing.domain.errors import (
    InvalidEmail,
    InvalidEmissionPointCode,
    InvalidEstablishmentCode,
)

_EMAIL_PATTERN: Final = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CODE_PATTERN: Final = re.compile(r"^\d{3}$")


@dataclass(slots=True)
class FiscalProfile:
    """A workshop's fiscal data (AD-3), mirroring
    `taller.invoicing.adapters.models.FiscalProfileModel`'s columns.
    """

    workshop_id: uuid.UUID
    rtn: str
    legal_name: str
    trade_name: str
    address: str
    phone: str
    email: str
    establishment_code: str
    emission_point_code: str
    created_at: datetime
    updated_at: datetime

    @property
    def is_complete(self) -> bool:
        """Every Art. 10-11 field is present (AD-3).

        A `PUT` already requires all of them, so this is a defensive
        invariant rather than a state that can drift: `get_settings`
        treats "no row" and "an incomplete row" the same way, through
        this one predicate, instead of two rules that could disagree.
        """
        return all(
            (
                self.rtn,
                self.legal_name,
                self.trade_name,
                self.address,
                self.phone,
                self.email,
                self.establishment_code,
                self.emission_point_code,
            )
        )


def normalize_email(raw: str) -> str:
    """Normalize and validate an email address (AD-3).

    Raises:
        InvalidEmail: ``raw`` is not a plausible ``local@domain.tld``
            address.
    """
    cleaned = raw.strip()
    if not _EMAIL_PATTERN.fullmatch(cleaned):
        raise InvalidEmail(raw)
    return cleaned


def normalize_establishment_code(raw: str) -> str:
    """Raises: InvalidEstablishmentCode: ``raw`` is not exactly 3 digits."""
    cleaned = raw.strip()
    if not _CODE_PATTERN.fullmatch(cleaned):
        raise InvalidEstablishmentCode(raw)
    return cleaned


def normalize_emission_point_code(raw: str) -> str:
    """Raises: InvalidEmissionPointCode: ``raw`` is not exactly 3 digits."""
    cleaned = raw.strip()
    if not _CODE_PATTERN.fullmatch(cleaned):
        raise InvalidEmissionPointCode(raw)
    return cleaned

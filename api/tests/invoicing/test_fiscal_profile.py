"""Tests for the fiscal profile's completeness predicate (AD-3).

Defect it catches: `FiscalProfile.is_complete` silently dropping one of
the Art. 10-11 fields from its check, so a profile missing that field
would be reported complete and invoicing would stay available when it
must not be (`fiscal-profile`, "A profile missing one field is
incomplete").
"""

import uuid
from datetime import UTC, datetime

import pytest

from taller.invoicing.domain.profile import FiscalProfile

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _complete_profile(**overrides: object) -> FiscalProfile:
    fields: dict[str, object] = {
        "workshop_id": uuid.uuid4(),
        "rtn": "08011990123456",
        "legal_name": "Taller Ana S. de R.L.",
        "trade_name": "Taller Ana",
        "address": "Col. Kennedy",
        "phone": "22000000",
        "email": "demo@example.invalid",
        "establishment_code": "001",
        "emission_point_code": "001",
        "created_at": _NOW,
        "updated_at": _NOW,
    }
    fields.update(overrides)
    return FiscalProfile(**fields)  # type: ignore[arg-type]


def test_a_profile_with_every_field_is_complete():
    assert _complete_profile().is_complete is True


@pytest.mark.parametrize(
    "field",
    [
        "rtn",
        "legal_name",
        "trade_name",
        "address",
        "phone",
        "email",
        "establishment_code",
        "emission_point_code",
    ],
)
def test_a_profile_missing_one_field_is_incomplete(field: str):
    profile = _complete_profile(**{field: ""})
    assert profile.is_complete is False

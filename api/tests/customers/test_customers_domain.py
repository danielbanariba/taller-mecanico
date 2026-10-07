"""Tests for `taller.customers.domain.entities.Customer.phone_is_mobile` and
`taller.customers.domain.plate.normalize_plate`.

Defect the phone tests catch: WhatsApp sharing (phase 2) is offered to a
landline because the mobile/landline split is wrong, or the app crashes
computing `phone_is_mobile` for a customer with no phone recorded at all.
"""

import uuid
from datetime import UTC, datetime

import pytest

from taller.customers.domain.entities import Customer
from taller.customers.domain.errors import InvalidPlate
from taller.customers.domain.plate import normalize_plate


def _customer(phone: str | None) -> Customer:
    now = datetime.now(UTC)
    return Customer(
        id=uuid.uuid4(),
        workshop_id=uuid.uuid4(),
        full_name="Maria Hernandez",
        phone=phone,
        notes=None,
        archived_at=None,
        created_at=now,
        updated_at=now,
    )


def test_a_landline_first_digit_is_not_mobile() -> None:
    assert _customer("22345678").phone_is_mobile is False


def test_a_non_landline_first_digit_is_mobile() -> None:
    assert _customer("98765432").phone_is_mobile is True


def test_no_phone_has_no_mobile_classification() -> None:
    assert _customer(None).phone_is_mobile is None


def test_a_plate_with_a_separator_and_lowercase_letters_is_normalized() -> None:
    """Defect this catches: a separator or lowercase variant bypasses the
    per-workshop active-plate uniqueness index, letting two vehicles share
    what is really the same plate.
    """
    assert normalize_plate("hab-1234") == "HAB1234"


def test_a_whitespace_only_plate_normalizes_to_no_plate() -> None:
    """Defect this catches: a whitespace-only plate is stored as `""`,
    which would collide with a second unplated vehicle against the
    partial unique index (both read as the empty string instead of NULL).
    """
    assert normalize_plate("  ") is None


def test_an_invalid_character_in_a_plate_is_rejected() -> None:
    """Defect this catches: an invalid character is silently accepted and
    stored instead of being rejected before it ever reaches the database.
    """
    with pytest.raises(InvalidPlate):
        normalize_plate("HAB#1")

"""Tests for `taller.customers.domain.entities.Customer.phone_is_mobile`.

Defect this catches: WhatsApp sharing (phase 2) is offered to a landline
because the mobile/landline split is wrong, or the app crashes computing
`phone_is_mobile` for a customer with no phone recorded at all.
"""

import uuid
from datetime import UTC, datetime

from taller.customers.domain.entities import Customer


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

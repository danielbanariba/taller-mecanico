"""Tests for the SQLAlchemy login throttle repository's row locking.

Defect this catches: reading a phone's throttle state without locking it,
so two concurrent failed logins both read the same count, both write
count + 1, and one failure is lost (an attacker gets extra guesses by
sending them in parallel).

Uses two real connections, unlike the rest of the suite (one connection per
test): a lock only shows up between two transactions. The row it needs is
committed, so the test deletes it again on the way out.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from taller.identity.adapters.repositories import SqlAlchemyLoginThrottleRepository
from taller.identity.domain.phone_number import PhoneNumber

PHONE = PhoneNumber("87650001")


@pytest.fixture
def committed_throttle_row(test_engine: Engine) -> Generator[None]:
    with test_engine.begin() as connection:
        connection.execute(
            text("INSERT INTO login_throttles (phone, failed_attempts) VALUES (:phone, 2)"),
            {"phone": PHONE.value},
        )
    try:
        yield
    finally:
        with test_engine.begin() as connection:
            connection.execute(
                text("DELETE FROM login_throttles WHERE phone = :phone"), {"phone": PHONE.value}
            )


@pytest.mark.usefixtures("committed_throttle_row")
def test_a_phone_being_checked_is_locked_against_a_concurrent_attempt(
    test_engine: Engine,
) -> None:
    with Session(test_engine) as first, Session(test_engine) as second:
        throttle = SqlAlchemyLoginThrottleRepository(first).get_for_update(PHONE)
        assert throttle.failed_attempts == 2

        # Fail fast instead of waiting forever for `first` to finish.
        second.execute(text("SET LOCAL lock_timeout = '200ms'"))
        with pytest.raises(OperationalError, match="lock timeout"):
            SqlAlchemyLoginThrottleRepository(second).get_for_update(PHONE)

"""Tests for the per-phone lockout on POST /api/auth/login.

Defects these catch:
- a failed attempt that is rolled back together with the 401 it produced
  (the request never commits it), so the counter never reaches the limit
  and the lockout exists only on paper;
- a locked phone whose password is still checked, letting an attacker keep
  guessing (or a correct guess in) while the phone is locked;
- throttling only registered phones, which lets anyone learn which phone
  numbers have accounts by watching which ones get locked out;
- a successful login that does not clear earlier failures, locking out the
  owner after a few typos spread over days;
- a lockout that never expires, or that leaves the counter at the limit so
  the first typo after it locks the phone again;
- a ``Retry-After`` that does not reflect the time actually left on the lock.
"""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from taller.identity.adapters.dependencies import get_clock
from taller.identity.domain.login_throttle import LOCKOUT_DURATION, MAX_FAILED_LOGINS
from taller.main import app

WRONG_PASSWORD = "not-the-right-password"


class FakeClock:
    """A clock that only moves when a test moves it."""

    def __init__(self, start: datetime) -> None:
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


@pytest.fixture
def clock() -> Generator[FakeClock]:
    fake = FakeClock(datetime(2026, 1, 15, 9, 0, tzinfo=UTC))
    app.dependency_overrides[get_clock] = lambda: fake
    try:
        yield fake
    finally:
        app.dependency_overrides.pop(get_clock, None)


def _login(client: TestClient, phone: str, password: str):
    return client.post("/api/auth/login", json={"phone": phone, "password": password})


def _fail_logins(client: TestClient, phone: str, times: int) -> None:
    for _ in range(times):
        response = _login(client, phone, WRONG_PASSWORD)
        assert response.status_code == 401, response.text


def test_the_limit_of_failed_logins_locks_the_phone_even_for_the_correct_password(
    client: TestClient, register_payload: dict, clock: FakeClock
) -> None:
    client.post("/api/auth/register", json=register_payload)
    client.cookies.clear()
    _fail_logins(client, register_payload["phone"], MAX_FAILED_LOGINS)

    response = _login(client, register_payload["phone"], register_payload["password"])

    assert response.status_code == 429
    assert response.json() == {"detail": "too_many_login_attempts"}
    assert int(response.headers["Retry-After"]) == int(LOCKOUT_DURATION.total_seconds())
    assert client.cookies.get("taller_session") is None


def test_an_unregistered_phone_is_locked_out_exactly_like_a_registered_one(
    client: TestClient, register_payload: dict, clock: FakeClock
) -> None:
    client.post("/api/auth/register", json=register_payload)
    client.cookies.clear()
    unregistered_phone = "22334455"
    _fail_logins(client, register_payload["phone"], MAX_FAILED_LOGINS)
    _fail_logins(client, unregistered_phone, MAX_FAILED_LOGINS)

    registered = _login(client, register_payload["phone"], WRONG_PASSWORD)
    unregistered = _login(client, unregistered_phone, WRONG_PASSWORD)

    assert unregistered.status_code == registered.status_code == 429
    assert unregistered.json() == registered.json()
    assert unregistered.headers["Retry-After"] == registered.headers["Retry-After"]


def test_a_successful_login_clears_earlier_failures(
    client: TestClient, register_payload: dict, clock: FakeClock
) -> None:
    client.post("/api/auth/register", json=register_payload)
    client.cookies.clear()
    phone, password = register_payload["phone"], register_payload["password"]
    _fail_logins(client, phone, MAX_FAILED_LOGINS - 1)
    assert _login(client, phone, password).status_code == 200

    # Without the reset, the first of these would reach the limit and the
    # rest (and the login after them) would be refused with 429.
    _fail_logins(client, phone, MAX_FAILED_LOGINS - 1)

    assert _login(client, phone, password).status_code == 200


def test_retry_after_counts_down_the_time_left_on_the_lock(
    client: TestClient, clock: FakeClock
) -> None:
    phone = "33445566"
    _fail_logins(client, phone, MAX_FAILED_LOGINS)
    clock.advance(timedelta(minutes=10))

    response = _login(client, phone, WRONG_PASSWORD)

    assert response.status_code == 429
    expected = LOCKOUT_DURATION - timedelta(minutes=10)
    assert int(response.headers["Retry-After"]) == int(expected.total_seconds())


def test_the_lock_expires_and_the_count_starts_again_from_zero(
    client: TestClient, register_payload: dict, clock: FakeClock
) -> None:
    client.post("/api/auth/register", json=register_payload)
    client.cookies.clear()
    phone, password = register_payload["phone"], register_payload["password"]
    _fail_logins(client, phone, MAX_FAILED_LOGINS)
    clock.advance(LOCKOUT_DURATION)

    # One typo right after the lock expires must not lock the phone again.
    _fail_logins(client, phone, 1)

    assert _login(client, phone, password).status_code == 200

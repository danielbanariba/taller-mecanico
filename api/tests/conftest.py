"""Shared pytest fixtures: a real Postgres test database, migrated once per
session, with per-test transactional isolation and an HTTP client wired to it.
"""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

# Settings() is constructed at import time (see taller.shared.db), so the
# JWT secret and cookie flag must be in the environment *before* taller.main
# is imported below. TALLER_JWT_SECRET has no default (it must be a real
# secret in every real environment), and TALLER_COOKIE_SECURE must be false
# here because TestClient talks to the app over plain HTTP: a browser (and
# httpx's cookie jar) never sends a Secure cookie back over a non-HTTPS
# connection, which would silently break every cookie-authenticated test.
os.environ.setdefault("TALLER_JWT_SECRET", "test-only-jwt-secret-value-needs-32-chars-minimum")
os.environ.setdefault("TALLER_COOKIE_SECURE", "false")

from taller.main import app  # noqa: E402
from taller.shared.db import get_db  # noqa: E402

API_ROOT = Path(__file__).resolve().parent.parent
TEST_DATABASE_URL = os.environ.get(
    "TALLER_TEST_DATABASE_URL",
    "postgresql+psycopg://taller:taller@localhost:5440/taller_test",
)


def _require_reachable_database(url: str) -> None:
    probe_engine = create_engine(url)
    try:
        with probe_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError:
        pytest.exit(
            "Cannot reach the test database at "
            f"{url}.\nStart it with `docker compose up -d db` (from the repo "
            "root) before running the test suite.",
            returncode=1,
        )
    finally:
        probe_engine.dispose()


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine]:
    """Migrate the test database once per session and expose its engine."""
    _require_reachable_database(TEST_DATABASE_URL)

    previous_url = os.environ.get("TALLER_DATABASE_URL")
    os.environ["TALLER_DATABASE_URL"] = TEST_DATABASE_URL
    try:
        alembic_cfg = Config(str(API_ROOT / "alembic.ini"))
        command.upgrade(alembic_cfg, "head")
    finally:
        if previous_url is None:
            os.environ.pop("TALLER_DATABASE_URL", None)
        else:
            os.environ["TALLER_DATABASE_URL"] = previous_url

    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session]:
    """One connection + outer transaction per test, rolled back on teardown.

    The Session joins that outer transaction using SAVEPOINTs
    (join_transaction_mode="create_savepoint"), so code under test is free to
    call commit()/rollback() without ever persisting data beyond the test.
    """
    connection = test_engine.connect()
    outer_transaction = connection.begin()
    session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")()
    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    """A TestClient whose DB dependency is overridden with the test session."""

    def _override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def register_payload() -> dict[str, str]:
    """A valid /api/auth/register request body for a fresh workshop owner."""
    return {
        "workshop_name": "Taller Don Chepe",
        "owner_name": "Chepe Martinez",
        "phone": "9988-7766",
        "password": "a-strong-enough-password",
    }


@pytest.fixture
def authenticated_client(client: TestClient, register_payload: dict[str, str]) -> TestClient:
    """A ``client`` that has just registered a workshop and is logged in.

    The session cookie from ``/api/auth/register`` stays in the client's
    cookie jar, so every later request through this fixture is authenticated
    as that workshop's owner. Reuse this fixture in any feature (e.g.
    inventory) that needs a tenant-scoped, already-authenticated client
    instead of registering a workshop by hand in every test.
    """
    response = client.post("/api/auth/register", json=register_payload)
    assert response.status_code == 201
    return client

"""Tests for GET /api/health.

Defects these catch:
- a health check that reports "ok" without ever querying the database
  (e.g. a hardcoded response), or crashes instead of answering; and
- a health check that swallows database errors and still reports "ok"
  when the database is actually unreachable, instead of returning 503.
"""

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from taller.main import app
from taller.shared.db import get_db


def test_health_reports_ok_when_database_is_reachable(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_degraded_when_database_is_unreachable() -> None:
    # Port 1 is never a Postgres listener, so this connection fails fast.
    unreachable_engine = create_engine(
        "postgresql+psycopg://taller:taller@localhost:1/taller",
        connect_args={"connect_timeout": 1},
    )
    unreachable_session_factory = sessionmaker(bind=unreachable_engine)

    def _override_get_db() -> Generator[Session]:
        session = unreachable_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as unreachable_client:
            response = unreachable_client.get("/api/health")
    finally:
        app.dependency_overrides.pop(get_db, None)
        unreachable_engine.dispose()

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}
    assert "localhost" not in response.text

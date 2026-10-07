"""Tests for the workshop-scoped data export (`GET /api/export`).

Defects these catch:
- an entity is missing from the archive;
- a tenant leak, or a client-supplied scope parameter overriding the
  authenticated workshop;
- the export has a side effect (creates, modifies, or deletes a record), or
  is non-deterministic absent writes.
"""

import io
import uuid
import zipfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from taller.main import app

_EXPORTED_ENTITIES = (
    "customers",
    "vehicles",
    "inventory_items",
    "inventory_movements",
    "work_orders",
    "work_order_lines",
    "payments",
)


@pytest.fixture
def second_authenticated_client(client: TestClient) -> Generator[TestClient]:
    """A second `TestClient`, authenticated as an independent second
    workshop. Mirrors `test_payments_api.second_authenticated_client`.
    """
    with TestClient(app) as second_client:
        response = second_client.post(
            "/api/auth/register",
            json={
                "workshop_name": "Taller Rival Export",
                "owner_name": "Otra Persona",
                "phone": "97712233",
                "password": "another-strong-password",
            },
        )
        assert response.status_code == 201
        yield second_client


def _create_customer(client: TestClient, **overrides: object) -> dict:
    payload = {"id": str(uuid.uuid4()), "full_name": "Maria Hernandez"}
    payload.update(overrides)
    response = client.post("/api/customers", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _export(client: TestClient, **params: object) -> bytes:
    response = client.get("/api/export", params=params)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/zip"
    return response.content


def _row_counts(db_session: Session) -> dict[str, int]:
    return {
        table: db_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()  # noqa: S608
        for table in _EXPORTED_ENTITIES
    }


def test_the_export_contains_exactly_one_csv_per_entity(authenticated_client: TestClient) -> None:
    _create_customer(authenticated_client)

    archive = zipfile.ZipFile(io.BytesIO(_export(authenticated_client)))

    assert sorted(archive.namelist()) == sorted(
        [
            "customers.csv",
            "vehicles.csv",
            "items.csv",
            "inventory_movements.csv",
            "work_orders.csv",
            "work_order_lines.csv",
            "payments.csv",
        ]
    )


def test_only_the_requesting_workshops_rows_appear(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    _create_customer(authenticated_client, full_name="Maria Hernandez")
    _create_customer(second_authenticated_client, full_name="Jose Rival")

    archive = zipfile.ZipFile(io.BytesIO(_export(authenticated_client)))
    customers_csv = archive.read("customers.csv").decode("utf-8-sig")

    assert "Maria Hernandez" in customers_csv
    assert "Jose Rival" not in customers_csv


def test_a_client_supplied_workshop_id_parameter_is_ignored(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    _create_customer(authenticated_client, full_name="Maria Hernandez")
    foreign = _create_customer(second_authenticated_client, full_name="Jose Rival")

    archive = zipfile.ZipFile(io.BytesIO(_export(authenticated_client, workshop_id=foreign["id"])))
    customers_csv = archive.read("customers.csv").decode("utf-8-sig")

    assert "Jose Rival" not in customers_csv
    assert "Maria Hernandez" in customers_csv


def test_two_consecutive_exports_yield_the_same_rows_with_no_side_effects(
    authenticated_client: TestClient, db_session: Session
) -> None:
    _create_customer(authenticated_client)
    before = _row_counts(db_session)

    first = _export(authenticated_client)
    second = _export(authenticated_client)

    after = _row_counts(db_session)
    assert first == second
    assert before == after

"""Tests for the workshop-scoped data export (`GET /api/export`).

Defects these catch:
- an entity is missing from the archive;
- a tenant leak, or a client-supplied scope parameter overriding the
  authenticated workshop;
- the export has a side effect (creates, modifies, or deletes a record), or
  is non-deterministic absent writes.
"""

import csv
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


def _create_vehicle(client: TestClient, *, customer_id: str, **overrides: object) -> dict:
    payload = {"customer_id": customer_id, "vehicle_type": "car", "make": "Toyota"}
    payload.update(overrides)
    response = client.post("/api/vehicles", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_order(client: TestClient, *, vehicle_id: str) -> dict:
    response = client.post(
        "/api/work-orders", json={"id": str(uuid.uuid4()), "vehicle_id": vehicle_id}
    )
    assert response.status_code == 201, response.text
    return response.json()


def _voided_payment_order(client: TestClient) -> dict:
    """A work order with exactly one payment that has since been voided."""
    customer = _create_customer(client)
    vehicle = _create_vehicle(client, customer_id=customer["id"])
    order = _create_order(client, vehicle_id=vehicle["id"])
    line = client.post(
        f"/api/work-orders/{order['id']}/lines",
        json={
            "id": str(uuid.uuid4()),
            "kind": "labor",
            "description": "Cambio de aceite",
            "quantity": 1,
            "unit_price_cents": 50000,
        },
    )
    assert line.status_code == 201, line.text
    approve = client.put(f"/api/work-orders/{order['id']}/status", json={"status": "approved"})
    assert approve.status_code == 200, approve.text

    payment_id = str(uuid.uuid4())
    created = client.post(
        f"/api/work-orders/{order['id']}/payments",
        json={"id": payment_id, "amount_cents": 50000, "method": "cash"},
    )
    assert created.status_code == 201, created.text
    voided = client.post(
        f"/api/work-orders/{order['id']}/payments/{payment_id}/void", json={"reason": "duplicado"}
    )
    assert voided.status_code == 200, voided.text
    return order


def _read_csv_rows(archive: zipfile.ZipFile, filename: str) -> list[dict[str, str]]:
    text_content = archive.read(filename).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text_content)))


def test_a_voided_payment_is_exported_with_its_void_columns(
    authenticated_client: TestClient,
) -> None:
    """Defect this catches: `payments.csv` dropping `voided_at`/`void_reason`
    makes a voided row indistinguishable from a real one. `work_orders.csv`'s
    own `paid_hnl` already excludes voided payments (per the `payments` spec's
    non-voided-only paid total), so without these columns summing
    `payments.csv` in Excel overstates recorded revenue by every voided
    amount, and the two CSVs in the same ZIP cannot be reconciled.
    """
    order = _voided_payment_order(authenticated_client)

    archive = zipfile.ZipFile(io.BytesIO(_export(authenticated_client)))
    payments_rows = _read_csv_rows(archive, "payments.csv")
    work_orders_rows = _read_csv_rows(archive, "work_orders.csv")

    assert len(payments_rows) == 1
    assert payments_rows[0]["order_id"] == order["id"]
    assert payments_rows[0]["voided_at"] != ""
    assert payments_rows[0]["void_reason"] == "duplicado"
    assert len(work_orders_rows) == 1
    assert work_orders_rows[0]["paid_hnl"] == "0.00"

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
from datetime import date, timedelta

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

#: Mirrors `test_credit_notes_api._PROFILE_PAYLOAD`.
_PROFILE_PAYLOAD = {
    "rtn": "0801-1990-123456",
    "legal_name": "Taller Don Chepe S. de R.L.",
    "trade_name": "Taller Don Chepe",
    "address": "Barrio El Centro, Tegucigalpa",
    "phone": "2200-1100",
    "email": "contacto@tallerdonchepe.example",
    "establishment_code": "001",
    "emission_point_code": "001",
}


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
    """Defect it catches: a new entity (here, the three fiscal document
    CSVs added for phase B) is left out of "Exportar todo" (`data-export`
    delta, "The export contains one file per entity").
    """
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
            "fiscal_invoices.csv",
            "fiscal_invoice_lines.csv",
            "fiscal_credit_notes.csv",
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


# --- Fiscal documents (phase B, `data-export` spec, design.md's AD-19) ---


def _save_profile(client: TestClient, **overrides: object) -> dict:
    """Mirrors `test_credit_notes_api._save_profile`."""
    payload = dict(_PROFILE_PAYLOAD)
    payload.update(overrides)
    response = client.put("/api/invoicing/profile", json=payload)
    assert response.status_code in (200, 201), response.text
    return response.json()


def _range_payload(**overrides: object) -> dict:
    """Mirrors `test_credit_notes_api._range_payload`."""
    payload = {
        "id": str(uuid.uuid4()),
        "document_type": "01",
        "cai": "A1B2C3D4E5",
        "range_start": 1,
        "range_end": 100,
        "issue_deadline": (date.today() + timedelta(days=300)).isoformat(),
    }
    payload.update(overrides)
    return payload


def _create_range(client: TestClient, **overrides: object) -> dict:
    response = client.post("/api/invoicing/cai-ranges", json=_range_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def _configure_invoicing_and_credit_notes(client: TestClient) -> None:
    """A complete fiscal profile plus one active `01` range and one `06`
    range -- the gates `issue_invoice` and `issue_credit_note` each need.
    """
    _save_profile(client)
    _create_range(client)
    _create_range(client, id=str(uuid.uuid4()), document_type="06", cai="B2C3D4E5F6")


def _order_in_status(client: TestClient, *, status: str) -> dict:
    """A work order with one labor line, walked through the status
    machine up to ``status`` (`quote -> approved -> in_progress ->
    completed -> delivered`).
    """
    customer = _create_customer(client, full_name="Comprador de Prueba")
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
    for target in ("approved", "in_progress", "completed", "delivered"):
        response = client.put(f"/api/work-orders/{order['id']}/status", json={"status": target})
        assert response.status_code == 200, response.text
        if target == status:
            return order
    raise AssertionError(f"Unreachable status: {status!r}")


def _issue_invoice(client: TestClient, order_id: str, **overrides: object) -> dict:
    payload = {"id": str(uuid.uuid4()), "order_id": order_id}
    payload.update(overrides)
    response = client.post("/api/invoicing/invoices", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _issue_credit_note(client: TestClient, invoice_id: str, **overrides: object) -> dict:
    payload = {
        "id": str(uuid.uuid4()),
        "invoice_id": invoice_id,
        "reason": "Servicio cancelado por el cliente",
    }
    payload.update(overrides)
    response = client.post("/api/invoicing/credit-notes", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_fiscal_invoices_csv_lists_only_the_current_workshops_documents(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    """Defect it catches: a missing `workshop_id` filter on the new
    fiscal sources leaks another workshop's legal documents.
    """
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    own_invoice = _issue_invoice(authenticated_client, order["id"])

    _configure_invoicing_and_credit_notes(second_authenticated_client)
    foreign_order = _order_in_status(second_authenticated_client, status="completed")
    _issue_invoice(second_authenticated_client, foreign_order["id"])

    archive = zipfile.ZipFile(io.BytesIO(_export(authenticated_client)))
    rows = _read_csv_rows(archive, "fiscal_invoices.csv")

    assert [row["number"] for row in rows] == [own_invoice["number"]]


def test_a_credit_notes_csv_row_references_its_invoice(authenticated_client: TestClient) -> None:
    """Defect it catches: the credit notes CSV drops `invoice_id`, so an
    issued Nota de Crédito cannot be traced back to the Factura it
    corrects (`credit-notes`, "A full credit note references its
    original Factura").
    """
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"])
    credit_note = _issue_credit_note(authenticated_client, invoice["id"])

    archive = zipfile.ZipFile(io.BytesIO(_export(authenticated_client)))
    rows = _read_csv_rows(archive, "fiscal_credit_notes.csv")

    assert len(rows) == 1
    assert rows[0]["number"] == credit_note["number"]
    assert rows[0]["invoice_id"] == invoice["id"]


def test_invoice_lines_reflect_the_snapshot_not_the_orders_current_lines(
    authenticated_client: TestClient,
) -> None:
    """Defect it catches: the invoice lines CSV reads the order's live
    `work_order_lines` instead of the immutable `fiscal_invoice_lines`
    snapshot, so a line added after a credit note reopened the order
    for editing would wrongly appear as if it had been invoiced
    (`data-export` delta, "Invoice lines reflect the snapshot, not the
    order's current lines").
    """
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"])
    _issue_credit_note(authenticated_client, invoice["id"])

    added = authenticated_client.post(
        f"/api/work-orders/{order['id']}/lines",
        json={
            "id": str(uuid.uuid4()),
            "kind": "labor",
            "description": "Línea añadida después de la nota de crédito",
            "quantity": 1,
            "unit_price_cents": 20000,
        },
    )
    assert added.status_code == 201, added.text

    archive = zipfile.ZipFile(io.BytesIO(_export(authenticated_client)))
    rows = _read_csv_rows(archive, "fiscal_invoice_lines.csv")

    assert len(rows) == 1
    assert rows[0]["invoice_id"] == invoice["id"]
    assert rows[0]["description"] == "Cambio de aceite"


def test_a_credit_note_reason_starting_with_equals_is_escaped(
    authenticated_client: TestClient,
) -> None:
    """Defect it catches: a crafted reason starting with `=` is read by
    Excel/Sheets as a formula instead of literal text -- the classic
    CSV formula-injection vector (`data-export`'s formula-injection
    guard, applied here to the new `reason` text column).
    """
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"])
    _issue_credit_note(authenticated_client, invoice["id"], reason="=cmd|'/c calc'!A1")

    archive = zipfile.ZipFile(io.BytesIO(_export(authenticated_client)))
    rows = _read_csv_rows(archive, "fiscal_credit_notes.csv")

    assert rows[0]["reason"] == "'=cmd|'/c calc'!A1"


def test_customers_csv_carries_billing_name_and_rtn_empty_when_absent(
    authenticated_client: TestClient,
) -> None:
    """Defect it catches: the customers CSV leaves out a customer's
    billing name and RTN, so the new fiscal fields are not available in
    "Exportar todo" (`data-export` delta, "A customer's billing data is
    exported").
    """
    _create_customer(
        authenticated_client,
        full_name="Repuestos El Sol",
        billing_name="Repuestos El Sol S. de R.L.",
        rtn="0801-1990-123456",
    )
    _create_customer(authenticated_client, full_name="Sin Datos Fiscales")

    archive = zipfile.ZipFile(io.BytesIO(_export(authenticated_client)))
    rows = {row["full_name"]: row for row in _read_csv_rows(archive, "customers.csv")}

    assert rows["Repuestos El Sol"]["billing_name"] == "Repuestos El Sol S. de R.L."
    assert rows["Repuestos El Sol"]["rtn"] == "08011990123456"
    assert rows["Sin Datos Fiscales"]["billing_name"] == ""
    assert rows["Sin Datos Fiscales"]["rtn"] == ""

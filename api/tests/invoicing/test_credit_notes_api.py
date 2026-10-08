"""Tests for issuing a Nota de Crédito against an issued Factura
(`credit-notes` and `cai-ranges` specs, design.md's AD-13).
"""

import uuid
from collections.abc import Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from taller.main import app

#: Mirrors `test_issue_invoice_api._PROFILE_PAYLOAD`.
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
    """Mirrors `test_issue_invoice_api.second_authenticated_client`."""
    with TestClient(app) as second_client:
        response = second_client.post(
            "/api/auth/register",
            json={
                "workshop_name": "Taller Rival",
                "owner_name": "Otra Persona",
                "phone": "99001122",
                "password": "another-strong-password",
            },
        )
        assert response.status_code == 201
        yield second_client


def _save_profile(client: TestClient, **overrides: object) -> dict:
    payload = dict(_PROFILE_PAYLOAD)
    payload.update(overrides)
    response = client.put("/api/invoicing/profile", json=payload)
    assert response.status_code in (200, 201), response.text
    return response.json()


def _range_payload(**overrides: object) -> dict:
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


def _create_customer(client: TestClient, **overrides: object) -> dict:
    payload = {"full_name": "Maria Hernandez"}
    payload.update(overrides)
    response = client.post("/api/customers", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_vehicle(client: TestClient, *, customer_id: str, **overrides: object) -> dict:
    payload = {"customer_id": customer_id, "vehicle_type": "car", "make": "Toyota"}
    payload.update(overrides)
    response = client.post("/api/vehicles", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _active_vehicle(client: TestClient, **customer_overrides: object) -> dict:
    customer = _create_customer(client, **customer_overrides)
    return _create_vehicle(client, customer_id=customer["id"])


def _create_order(client: TestClient, *, vehicle_id: str, **overrides: object) -> dict:
    payload = {"id": str(uuid.uuid4()), "vehicle_id": vehicle_id}
    payload.update(overrides)
    response = client.post("/api/work-orders", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _labor_line(**overrides: object) -> dict:
    payload = {
        "id": str(uuid.uuid4()),
        "kind": "labor",
        "description": "Cambio de aceite",
        "quantity": 1,
        "unit_price_cents": 50000,
    }
    payload.update(overrides)
    return payload


def _add_line(client: TestClient, order_id: str, line: dict) -> dict:
    response = client.post(f"/api/work-orders/{order_id}/lines", json=line)
    assert response.status_code in (200, 201), response.text
    return response.json()


def _set_status(client: TestClient, order_id: str, target: str) -> object:
    return client.put(f"/api/work-orders/{order_id}/status", json={"status": target})


def _get_order(client: TestClient, order_id: str) -> dict:
    response = client.get(f"/api/work-orders/{order_id}")
    assert response.status_code == 200, response.text
    return response.json()


def _order_in_status(client: TestClient, *, status: str, unit_price_cents: int = 50000) -> dict:
    """A work order with one labor line, walked through the status
    machine up to ``status`` (`quote -> approved -> in_progress ->
    completed -> delivered`).
    """
    vehicle = _active_vehicle(client)
    order = _create_order(client, vehicle_id=vehicle["id"])
    _add_line(client, order["id"], _labor_line(unit_price_cents=unit_price_cents))
    if status == "quote":
        return order
    for target in ("approved", "in_progress", "completed", "delivered"):
        response = _set_status(client, order["id"], target)
        assert response.status_code == 200, response.text
        if target == status:
            return response.json()
    raise AssertionError(f"Unreachable status: {status!r}")


def _issue_invoice(client: TestClient, order_id: str, **overrides: object) -> object:
    payload = {"id": str(uuid.uuid4()), "order_id": order_id}
    payload.update(overrides)
    return client.post("/api/invoicing/invoices", json=payload)


def _configure_invoicing_and_credit_notes(client: TestClient) -> None:
    """A complete fiscal profile plus one active, unexhausted,
    unexpired `01` range and one `06` range -- the gates `issue_invoice`
    and `issue_credit_note` each need before anything else.
    """
    _save_profile(client)
    _create_range(client)
    _create_range(client, id=str(uuid.uuid4()), document_type="06", cai="B2C3D4E5F6")


def _issue_credit_note(client: TestClient, invoice_id: str, **overrides: object) -> object:
    payload = {
        "id": str(uuid.uuid4()),
        "invoice_id": invoice_id,
        "reason": "Servicio cancelado por el cliente",
    }
    payload.update(overrides)
    return client.post("/api/invoicing/credit-notes", json=payload)


def test_a_full_credit_note_references_its_original_factura(authenticated_client: TestClient):
    """Defect it catches: a missing Art. 25-26 reference, or a
    mismatched amount.
    """
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"]).json()

    response = _issue_credit_note(authenticated_client, invoice["id"])

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["original_cai"] == invoice["cai"]
    assert body["original_number"] == invoice["number"]
    assert body["original_issue_date"] == invoice["issue_date"]
    assert body["buyer_name"] == invoice["buyer_name"]
    assert body["buyer_rtn"] == invoice["buyer_rtn"]
    assert body["total_cents"] == invoice["total_cents"]


def test_a_credit_note_with_no_reason_is_rejected(authenticated_client: TestClient):
    """Defect it catches: a reasonless correction is accepted."""
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"]).json()

    response = _issue_credit_note(authenticated_client, invoice["id"], reason="   ")

    assert response.status_code == 422
    assert response.json()["detail"] == "invalid_credit_note_reason"


def test_no_active_06_range_blocks_credit_note_issuance(authenticated_client: TestClient):
    """Defect it catches: the opt-in gate is bypassed for the
    correction type.
    """
    _save_profile(authenticated_client)
    _create_range(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"]).json()

    response = _issue_credit_note(authenticated_client, invoice["id"])

    assert response.status_code == 409
    assert response.json()["detail"] == "invoicing_not_configured"


def test_an_exhausted_06_range_blocks_issuance(authenticated_client: TestClient):
    """Defect it catches: exhaustion enforcement does not extend to
    credit notes.
    """
    _save_profile(authenticated_client)
    _create_range(authenticated_client)
    _create_range(
        authenticated_client,
        id=str(uuid.uuid4()),
        document_type="06",
        cai="B2C3D4E5F6",
        range_start=1,
        range_end=1,
    )
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"]).json()
    first = _issue_credit_note(authenticated_client, invoice["id"])
    assert first.status_code == 201, first.text

    other_order = _order_in_status(authenticated_client, status="completed")
    other_invoice = _issue_invoice(authenticated_client, other_order["id"]).json()
    response = _issue_credit_note(authenticated_client, other_invoice["id"])

    assert response.status_code == 409
    assert response.json()["detail"] == "cai_range_exhausted"


def test_a_second_credit_note_against_the_same_factura_is_rejected(
    authenticated_client: TestClient,
):
    """Defect it catches: double reversal of one sale."""
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"]).json()
    first = _issue_credit_note(authenticated_client, invoice["id"])
    assert first.status_code == 201, first.text

    second = _issue_credit_note(authenticated_client, invoice["id"])

    assert second.status_code == 409
    assert second.json()["detail"] == "credit_note_already_issued"


def test_replaying_an_identical_credit_note_is_a_noop(authenticated_client: TestClient):
    """Defect it catches: a retry burns a `06` correlative."""
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"]).json()
    payload = {
        "id": str(uuid.uuid4()),
        "invoice_id": invoice["id"],
        "reason": "Servicio cancelado por el cliente",
    }
    first = authenticated_client.post("/api/invoicing/credit-notes", json=payload)
    assert first.status_code == 201, first.text

    replay = authenticated_client.post("/api/invoicing/credit-notes", json=payload)
    assert replay.status_code == 200
    assert replay.json()["number"] == first.json()["number"]

    # The replay must not have consumed a second `06` correlative: a
    # fresh credit note against a different Factura still gets the
    # very next number.
    other_order = _order_in_status(authenticated_client, status="completed")
    other_invoice = _issue_invoice(authenticated_client, other_order["id"]).json()
    other = _issue_credit_note(authenticated_client, other_invoice["id"])
    assert other.status_code == 201, other.text
    assert other.json()["number"] != first.json()["number"]


def test_reusing_the_credit_note_id_for_a_different_invoice_is_a_conflict(
    authenticated_client: TestClient,
):
    """Defect it catches: a retried id silently attaches to the
    wrong Factura.
    """
    _configure_invoicing_and_credit_notes(authenticated_client)
    first_order = _order_in_status(authenticated_client, status="completed")
    first_invoice = _issue_invoice(authenticated_client, first_order["id"]).json()
    second_order = _order_in_status(authenticated_client, status="completed")
    second_invoice = _issue_invoice(authenticated_client, second_order["id"]).json()
    credit_note_id = str(uuid.uuid4())

    first = _issue_credit_note(authenticated_client, first_invoice["id"], id=credit_note_id)
    assert first.status_code == 201, first.text

    conflict = _issue_credit_note(authenticated_client, second_invoice["id"], id=credit_note_id)
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "credit_note_id_conflict"


def test_lines_become_editable_again_after_a_full_credit_note(authenticated_client: TestClient):
    """Defect it catches: the lock is not released, or re-invoicing
    collides with the stale partial-unique index.
    """
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"]).json()

    still_locked = authenticated_client.post(
        f"/api/work-orders/{order['id']}/lines", json=_labor_line()
    )
    assert still_locked.status_code == 409
    assert still_locked.json()["detail"] == "work_order_invoiced"

    credited = _issue_credit_note(authenticated_client, invoice["id"])
    assert credited.status_code == 201, credited.text

    add_response = authenticated_client.post(
        f"/api/work-orders/{order['id']}/lines", json=_labor_line()
    )
    assert add_response.status_code == 201, add_response.text

    new_invoice = _issue_invoice(authenticated_client, order["id"])
    assert new_invoice.status_code == 201, new_invoice.text
    assert new_invoice.json()["number"] != invoice["number"]


def test_a_delivered_fully_credited_order_may_be_reinvoiced_with_corrected_buyer_data(
    authenticated_client: TestClient,
):
    """Defect it catches: amount corrections sneak into a delivered
    order, or re-invoicing is blocked entirely.
    """
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="delivered")
    invoice = _issue_invoice(authenticated_client, order["id"]).json()
    credited = _issue_credit_note(authenticated_client, invoice["id"])
    assert credited.status_code == 201, credited.text

    line_payload = {
        "id": str(uuid.uuid4()),
        "kind": "labor",
        "description": "Linea extra",
        "quantity": 1,
        "unit_price_cents": 10000,
    }
    locked = authenticated_client.post(f"/api/work-orders/{order['id']}/lines", json=line_payload)
    assert locked.status_code == 409
    assert locked.json()["detail"] == "work_order_locked"

    corrected = _issue_invoice(
        authenticated_client,
        order["id"],
        buyer_name="Nombre Corregido",
        buyer_rtn="0801-1990-654321",
    )
    assert corrected.status_code == 201, corrected.text
    assert corrected.json()["total_cents"] == invoice["total_cents"]
    assert corrected.json()["buyer_name"] == "Nombre Corregido"


def test_a_credit_note_has_no_effect_on_payments_or_stock(authenticated_client: TestClient):
    """Defect it catches: a credit note voids or refunds a recorded
    payment, or restocks a part the order consumed (`credit-notes`
    spec's "Issuing a credit note leaves payments and stock untouched").
    """
    client = authenticated_client
    _configure_invoicing_and_credit_notes(client)
    item_response = client.post(
        "/api/inventory/items",
        json={
            "name": "Filtro de aceite",
            "category": "Filtros",
            "unit": "unidad",
            "initial_stock": 10,
        },
    )
    assert item_response.status_code == 201, item_response.text
    item_id = item_response.json()["id"]
    vehicle = _active_vehicle(client)
    order = _create_order(client, vehicle_id=vehicle["id"])
    _add_line(
        client,
        order["id"],
        {
            "id": str(uuid.uuid4()),
            "kind": "inventory_part",
            "item_id": item_id,
            "description": "Filtro de aceite",
            "quantity": 2,
            "unit_price_cents": 8000,
        },
    )
    for target in ("approved", "in_progress", "completed"):
        response = _set_status(client, order["id"], target)
        assert response.status_code == 200, response.text
    payment = client.post(
        f"/api/work-orders/{order['id']}/payments",
        json={"id": str(uuid.uuid4()), "amount_cents": 10000, "method": "cash"},
    )
    assert payment.status_code == 201, payment.text
    invoice = _issue_invoice(client, order["id"]).json()

    before = _get_order(client, order["id"])
    assert before["paid_cents"] == 10000
    assert client.get(f"/api/inventory/items/{item_id}").json()["stock"] == 8

    credited = _issue_credit_note(client, invoice["id"])
    assert credited.status_code == 201, credited.text

    after = _get_order(client, order["id"])
    assert after["payments"] == before["payments"]
    assert after["paid_cents"] == before["paid_cents"]
    assert after["balance_cents"] == before["balance_cents"]
    assert client.get(f"/api/inventory/items/{item_id}").json()["stock"] == 8


def test_editing_the_customer_after_a_credit_note_leaves_it_unchanged_on_reprint(
    authenticated_client: TestClient,
):
    """Defect it catches: a reprint renders from live data."""
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"]).json()
    issued = _issue_credit_note(authenticated_client, invoice["id"])
    assert issued.status_code == 201, issued.text
    credit_note_id = issued.json()["id"]
    before = authenticated_client.get(f"/api/invoicing/credit-notes/{credit_note_id}").json()

    customer_id = order["customer"]["id"]
    patch = authenticated_client.patch(
        f"/api/customers/{customer_id}", json={"full_name": "Nombre Cambiado"}
    )
    assert patch.status_code == 200, patch.text

    after = authenticated_client.get(f"/api/invoicing/credit-notes/{credit_note_id}").json()
    assert after == before


def test_a_bogus_invoice_id_is_not_found(authenticated_client: TestClient):
    """Defect it catches: a credit note against a nonexistent Factura
    silently succeeds instead of reporting it as missing (AD-13 step
    1).
    """
    _configure_invoicing_and_credit_notes(authenticated_client)
    response = _issue_credit_note(authenticated_client, str(uuid.uuid4()))
    assert response.status_code == 404
    assert response.json()["detail"] == "invoice_not_found"


def test_another_workshops_credit_note_is_invisible(
    authenticated_client: TestClient, second_authenticated_client: TestClient
):
    """Defect it catches: tenant leak."""
    _configure_invoicing_and_credit_notes(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    invoice = _issue_invoice(authenticated_client, order["id"]).json()
    issued = _issue_credit_note(authenticated_client, invoice["id"])
    assert issued.status_code == 201, issued.text
    credit_note_id = issued.json()["id"]

    foreign_response = second_authenticated_client.get(
        f"/api/invoicing/credit-notes/{credit_note_id}"
    )
    assert foreign_response.status_code == 404
    assert foreign_response.json()["detail"] == "credit_note_not_found"

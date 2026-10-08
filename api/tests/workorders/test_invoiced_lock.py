"""Tests for the line lock an invoiced work order gets once it has a
non-credited Factura (the `work-orders` delta, design.md's AD-2/AD-6).
"""

import uuid

from fastapi.testclient import TestClient


def _save_profile(client: TestClient) -> None:
    payload = {
        "rtn": "0801-1990-123456",
        "legal_name": "Taller Don Chepe S. de R.L.",
        "trade_name": "Taller Don Chepe",
        "address": "Barrio El Centro, Tegucigalpa",
        "phone": "2200-1100",
        "email": "contacto@tallerdonchepe.example",
        "establishment_code": "001",
        "emission_point_code": "001",
    }
    response = client.put("/api/invoicing/profile", json=payload)
    assert response.status_code in (200, 201), response.text


def _create_range(client: TestClient) -> None:
    from datetime import date, timedelta

    payload = {
        "id": str(uuid.uuid4()),
        "document_type": "01",
        "cai": "A1B2C3D4E5",
        "range_start": 1,
        "range_end": 100,
        "issue_deadline": (date.today() + timedelta(days=300)).isoformat(),
    }
    response = client.post("/api/invoicing/cai-ranges", json=payload)
    assert response.status_code == 201, response.text


def _configure_invoicing(client: TestClient) -> None:
    _save_profile(client)
    _create_range(client)


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


def _active_vehicle(client: TestClient) -> dict:
    customer = _create_customer(client)
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


def _add_line(client: TestClient, order_id: str, line: dict) -> object:
    return client.post(f"/api/work-orders/{order_id}/lines", json=line)


def _remove_line(client: TestClient, order_id: str, line_id: str) -> object:
    return client.delete(f"/api/work-orders/{order_id}/lines/{line_id}")


def _set_status(client: TestClient, order_id: str, target: str) -> object:
    return client.put(f"/api/work-orders/{order_id}/status", json={"status": target})


def _get_order(client: TestClient, order_id: str) -> dict:
    response = client.get(f"/api/work-orders/{order_id}")
    assert response.status_code == 200, response.text
    return response.json()


def _completed_order(client: TestClient, *, lines: int = 1) -> dict:
    """An order with ``lines`` labor lines, walked to `completed`."""
    vehicle = _active_vehicle(client)
    order = _create_order(client, vehicle_id=vehicle["id"])
    for _ in range(lines):
        response = _add_line(client, order["id"], _labor_line())
        assert response.status_code == 201, response.text
    for target in ("approved", "in_progress", "completed"):
        response = _set_status(client, order["id"], target)
        assert response.status_code == 200, response.text
    return response.json()


def _issue_invoice(client: TestClient, order_id: str) -> dict:
    payload = {"id": str(uuid.uuid4()), "order_id": order_id}
    response = client.post("/api/invoicing/invoices", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_adding_a_line_to_an_invoiced_order_is_rejected(authenticated_client: TestClient):
    """Defect it catches: the lock is missing."""
    _configure_invoicing(authenticated_client)
    order = _completed_order(authenticated_client)
    _issue_invoice(authenticated_client, order["id"])

    response = _add_line(authenticated_client, order["id"], _labor_line())

    assert response.status_code == 409
    assert response.json()["detail"] == "work_order_invoiced"
    after = _get_order(authenticated_client, order["id"])
    assert len(after["lines"]) == len(order["lines"])


def test_lines_editable_is_false_on_an_invoiced_order(authenticated_client: TestClient):
    """Defect it catches: the UI still offers an edit action the server
    will reject.
    """
    _configure_invoicing(authenticated_client)
    order = _completed_order(authenticated_client)
    assert order["lines_editable"] is True

    _issue_invoice(authenticated_client, order["id"])

    after = _get_order(authenticated_client, order["id"])
    assert after["status"] == "completed"
    assert after["lines_editable"] is False


def test_completed_to_delivered_still_succeeds_on_an_invoiced_order(
    authenticated_client: TestClient,
):
    """Defect it catches: the lock over-reaches into status transitions."""
    _configure_invoicing(authenticated_client)
    order = _completed_order(authenticated_client)
    _issue_invoice(authenticated_client, order["id"])

    response = _set_status(authenticated_client, order["id"], "delivered")

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "delivered"


def test_patching_order_fields_still_succeeds_while_invoiced(authenticated_client: TestClient):
    """Defect it catches: the lock over-reaches into non-line fields."""
    _configure_invoicing(authenticated_client)
    order = _completed_order(authenticated_client)
    _issue_invoice(authenticated_client, order["id"])

    response = authenticated_client.patch(
        f"/api/work-orders/{order['id']}",
        json={"notes": "Nota nueva", "complaint": "Ruido al frenar", "odometer_km": 12345},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["notes"] == "Nota nueva"
    assert body["complaint"] == "Ruido al frenar"
    assert body["odometer_km"] == 12345


def test_line_edits_on_a_delivered_noninvoiced_order_still_give_work_order_locked(
    authenticated_client: TestClient,
):
    """Regression check. Defect it catches: the new check shadows or
    replaces the existing delivered/cancelled lock's error code.
    """
    order = _completed_order(authenticated_client)
    delivered = _set_status(authenticated_client, order["id"], "delivered")
    assert delivered.status_code == 200, delivered.text

    response = _add_line(authenticated_client, order["id"], _labor_line())

    assert response.status_code == 409
    assert response.json()["detail"] == "work_order_locked"


def test_replaying_an_already_added_line_still_succeeds_on_an_invoiced_order(
    authenticated_client: TestClient,
):
    """Regression check. Defect it catches: the new lock turns a harmless
    retry into a 409.
    """
    _configure_invoicing(authenticated_client)
    order = _completed_order(authenticated_client)
    existing_line = order["lines"][0]
    _issue_invoice(authenticated_client, order["id"])

    replay_payload = {
        "id": existing_line["id"],
        "kind": existing_line["kind"],
        "description": existing_line["description"],
        "quantity": existing_line["quantity"],
        "unit_price_cents": existing_line["unit_price_cents"],
    }
    response = _add_line(authenticated_client, order["id"], replay_payload)

    assert response.status_code == 200, response.text


def test_removing_an_already_removed_line_still_succeeds_on_an_invoiced_order(
    authenticated_client: TestClient,
):
    """Regression check. Defect it catches: the new lock turns a harmless
    retry into a 409.
    """
    _configure_invoicing(authenticated_client)
    order = _completed_order(authenticated_client, lines=2)
    removed_line_id = order["lines"][0]["id"]
    remove_response = _remove_line(authenticated_client, order["id"], removed_line_id)
    assert remove_response.status_code == 200, remove_response.text

    _issue_invoice(authenticated_client, order["id"])

    replay_remove = _remove_line(authenticated_client, order["id"], removed_line_id)

    assert replay_remove.status_code == 200, replay_remove.text

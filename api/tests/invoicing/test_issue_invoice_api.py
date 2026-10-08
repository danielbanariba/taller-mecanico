"""Tests for issuing a Factura from an eligible work order
(`fiscal-invoices` and `cai-ranges` specs, design.md's AD-6/AD-7).
"""

import uuid
from collections.abc import Generator
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from taller.identity.adapters.dependencies import get_clock
from taller.main import app

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

#: `IDENTIFICATION_THRESHOLD_CENTS` (AD-11): L 10,000.00.
_IDENTIFICATION_THRESHOLD_CENTS = 1_000_000


class FakeClock:
    """A clock that only moves when a test moves it. Mirrors
    `test_login_throttling.FakeClock`.
    """

    def __init__(self, start: datetime) -> None:
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


@pytest.fixture
def second_authenticated_client(client: TestClient) -> Generator[TestClient]:
    """Mirrors `test_payments_api.second_authenticated_client`."""
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


def _configure_invoicing(client: TestClient, **range_overrides: object) -> dict:
    """A complete fiscal profile and one active, unexhausted, unexpired
    `01` range -- the gate `issue_invoice` needs before anything else.
    """
    _save_profile(client)
    return _create_range(client, **range_overrides)


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


def test_no_fiscal_profile_gives_invoicing_not_configured(authenticated_client: TestClient):
    """Defect it catches: issuance proceeds with no issuer data to
    snapshot ("No fiscal profile at all").
    """
    order = _order_in_status(authenticated_client, status="completed")
    response = _issue_invoice(authenticated_client, order["id"])
    assert response.status_code == 409
    assert response.json()["detail"] == "invoicing_not_configured"


def test_a_complete_profile_with_no_active_range_gives_invoicing_not_configured(
    authenticated_client: TestClient,
):
    """Defect it catches: the gate skips the range-missing case ("A
    complete profile but no active Factura range").
    """
    _save_profile(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    response = _issue_invoice(authenticated_client, order["id"])
    assert response.status_code == 409
    assert response.json()["detail"] == "invoicing_not_configured"


def test_both_conditions_met_allow_issuance(authenticated_client: TestClient):
    _configure_invoicing(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    response = _issue_invoice(authenticated_client, order["id"])
    assert response.status_code == 201, response.text


@pytest.mark.parametrize("status", ["quote", "approved", "in_progress"])
def test_issuing_from_an_unfinished_order_is_rejected(
    authenticated_client: TestClient, status: str
):
    """Defect it catches: unfinished work gets a legal document."""
    _configure_invoicing(authenticated_client)
    order = _order_in_status(authenticated_client, status=status)
    response = _issue_invoice(authenticated_client, order["id"])
    assert response.status_code == 409
    assert response.json()["detail"] == "work_order_not_invoiceable"


@pytest.mark.parametrize("status", ["completed", "delivered"])
def test_issuing_from_a_finished_order_succeeds(authenticated_client: TestClient, status: str):
    _configure_invoicing(authenticated_client)
    order = _order_in_status(authenticated_client, status=status)
    response = _issue_invoice(authenticated_client, order["id"])
    assert response.status_code == 201, response.text


def test_a_second_factura_while_the_first_is_not_credited_is_rejected(
    authenticated_client: TestClient,
):
    """Defect it catches: an order ends up with two live Facturas."""
    _configure_invoicing(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    first = _issue_invoice(authenticated_client, order["id"])
    assert first.status_code == 201, first.text

    second = _issue_invoice(authenticated_client, order["id"])
    assert second.status_code == 409
    assert second.json()["detail"] == "work_order_already_invoiced"


def test_below_the_identification_threshold_with_no_buyer_data_succeeds(
    authenticated_client: TestClient,
):
    _configure_invoicing(authenticated_client)
    order = _order_in_status(
        authenticated_client,
        status="completed",
        unit_price_cents=_IDENTIFICATION_THRESHOLD_CENTS - 100,
    )
    response = _issue_invoice(authenticated_client, order["id"])
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["buyer_name"] is None
    assert body["buyer_rtn"] is None


def test_at_the_identification_threshold_with_no_identification_is_rejected(
    authenticated_client: TestClient,
):
    """Defect it catches: the L 10,000 boundary is off by one."""
    _configure_invoicing(authenticated_client)
    order = _order_in_status(
        authenticated_client, status="completed", unit_price_cents=_IDENTIFICATION_THRESHOLD_CENTS
    )
    response = _issue_invoice(authenticated_client, order["id"])
    assert response.status_code == 422
    assert response.json()["detail"] == "buyer_identification_required"


def test_at_the_identification_threshold_with_identification_succeeds(
    authenticated_client: TestClient,
):
    _configure_invoicing(authenticated_client)
    order = _order_in_status(
        authenticated_client, status="completed", unit_price_cents=_IDENTIFICATION_THRESHOLD_CENTS
    )
    response = _issue_invoice(
        authenticated_client,
        order["id"],
        buyer_name="Maria Hernandez",
        buyer_rtn="0801-1990-123456",
    )
    assert response.status_code == 201, response.text


def test_the_tax_split_sums_exactly_and_the_order_is_unchanged(authenticated_client: TestClient):
    """Defect it catches: a snapshot field is missing, or the order
    response leaks tax.
    """
    _configure_invoicing(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed", unit_price_cents=115_000)
    before = _get_order(authenticated_client, order["id"])

    response = _issue_invoice(authenticated_client, order["id"])

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["taxable_15_cents"] == 100_000
    assert body["isv_15_cents"] == 15_000
    assert body["taxable_15_cents"] + body["isv_15_cents"] == body["total_cents"] == 115_000

    after = _get_order(authenticated_client, order["id"])
    assert after["total_cents"] == before["total_cents"] == 115_000
    assert after["paid_cents"] == before["paid_cents"]
    assert after["balance_cents"] == before["balance_cents"]


def test_the_number_is_assembled_from_the_profile_and_the_allocated_correlative(
    authenticated_client: TestClient,
):
    _configure_invoicing(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    response = _issue_invoice(authenticated_client, order["id"])
    assert response.status_code == 201, response.text
    assert response.json()["number"] == "001-001-01-00000001"


def test_replaying_an_identical_issuance_is_a_noop(authenticated_client: TestClient):
    """Defect it catches: a retry burns a correlative, a gap SAR would see."""
    _configure_invoicing(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    payload = {"id": str(uuid.uuid4()), "order_id": order["id"]}
    first = authenticated_client.post("/api/invoicing/invoices", json=payload)
    assert first.status_code == 201, first.text

    replay = authenticated_client.post("/api/invoicing/invoices", json=payload)
    assert replay.status_code == 200
    assert replay.json()["number"] == first.json()["number"]

    # The replay must not have consumed a second correlative: the next
    # order's Factura still gets the very next number.
    other_order = _order_in_status(authenticated_client, status="completed")
    other = _issue_invoice(authenticated_client, other_order["id"])
    assert other.status_code == 201, other.text
    assert other.json()["number"] == "001-001-01-00000002"


def test_reusing_the_invoice_id_for_a_different_order_is_a_conflict(
    authenticated_client: TestClient,
):
    _configure_invoicing(authenticated_client)
    first_order = _order_in_status(authenticated_client, status="completed")
    second_order = _order_in_status(authenticated_client, status="completed")
    invoice_id = str(uuid.uuid4())

    first = _issue_invoice(authenticated_client, first_order["id"], id=invoice_id)
    assert first.status_code == 201, first.text

    conflict = _issue_invoice(authenticated_client, second_order["id"], id=invoice_id)
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "fiscal_invoice_id_conflict"


def test_issuing_with_an_outstanding_balance_succeeds_and_the_balance_is_unaffected(
    authenticated_client: TestClient,
):
    _configure_invoicing(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed", unit_price_cents=50_000)
    before = _get_order(authenticated_client, order["id"])
    assert before["balance_cents"] == 50_000

    response = _issue_invoice(authenticated_client, order["id"])
    assert response.status_code == 201, response.text

    after = _get_order(authenticated_client, order["id"])
    assert after["balance_cents"] == before["balance_cents"] == 50_000


def test_editing_the_profile_after_issuance_leaves_the_invoice_byte_identical(
    authenticated_client: TestClient,
):
    """Defect it catches: a reprint renders from live data."""
    _configure_invoicing(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    issued = _issue_invoice(authenticated_client, order["id"])
    assert issued.status_code == 201, issued.text
    invoice_id = issued.json()["id"]
    before = authenticated_client.get(f"/api/invoicing/invoices/{invoice_id}").json()

    _save_profile(
        authenticated_client, legal_name="Otro Nombre Legal S.A.", address="Otra dirección"
    )

    after = authenticated_client.get(f"/api/invoicing/invoices/{invoice_id}").json()
    assert after == before


def test_editing_the_customer_after_issuance_leaves_the_invoice_byte_identical(
    authenticated_client: TestClient,
):
    _configure_invoicing(authenticated_client)
    order = _order_in_status(authenticated_client, status="completed")
    issued = _issue_invoice(authenticated_client, order["id"])
    assert issued.status_code == 201, issued.text
    invoice_id = issued.json()["id"]
    before = authenticated_client.get(f"/api/invoicing/invoices/{invoice_id}").json()

    customer_id = order["customer"]["id"]
    patch = authenticated_client.patch(
        f"/api/customers/{customer_id}", json={"full_name": "Nombre Cambiado"}
    )
    assert patch.status_code == 200, patch.text

    after = authenticated_client.get(f"/api/invoicing/invoices/{invoice_id}").json()
    assert after == before


@pytest.fixture
def clock() -> Generator[FakeClock]:
    fake = FakeClock(datetime(2026, 11, 1, 5, 59, tzinfo=UTC))
    app.dependency_overrides[get_clock] = lambda: fake
    try:
        yield fake
    finally:
        app.dependency_overrides.pop(get_clock, None)


def test_a_utc_day_boundary_does_not_cause_an_incorrect_allow_or_block(
    authenticated_client: TestClient, clock: FakeClock
):
    """Defect it catches: a UTC day boundary blocks or allows past the
    Honduran fecha límite evening.
    """
    _save_profile(authenticated_client)
    _create_range(authenticated_client, issue_deadline="2026-10-31")
    order = _order_in_status(authenticated_client, status="completed")

    still_the_deadline_day = _issue_invoice(authenticated_client, order["id"])
    assert still_the_deadline_day.status_code == 201, still_the_deadline_day.text
    assert still_the_deadline_day.json()["issue_date"] == "2026-10-31"

    clock.advance(timedelta(minutes=1))
    other_order = _order_in_status(authenticated_client, status="completed")
    past_the_deadline = _issue_invoice(authenticated_client, other_order["id"])
    assert past_the_deadline.status_code == 409
    assert past_the_deadline.json()["detail"] == "cai_range_expired"


def test_issuing_against_another_workshops_order_is_not_found(
    authenticated_client: TestClient, second_authenticated_client: TestClient
):
    """Defect it catches: tenant leak."""
    _configure_invoicing(second_authenticated_client)
    foreign_order = _order_in_status(second_authenticated_client, status="completed")

    response = _issue_invoice(authenticated_client, foreign_order["id"])
    assert response.status_code == 404
    assert response.json()["detail"] == "work_order_not_found"

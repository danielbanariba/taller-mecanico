"""Tests for the daily cash summary endpoint (GET /api/cash-summary).

Defects these catch:
- the day boundary uses UTC (or the server's own local time) instead of
  `America/Tegucigalpa`, so a payment recorded near local midnight is
  bucketed into the wrong calendar day;
- a payment method with no payments that day is missing from
  `totals_cents` instead of reporting 0, breaking the drawer
  reconciliation UI that expects all four keys;
- a tenant leak lets another workshop's payments into the summary;
- a voided payment still contributes to its method's total, the grand
  total, or the listed payments;
- a malformed `date` query parameter crashes instead of a clean 422.
"""

import uuid
from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from taller.main import app
from taller.workorders.adapters.models import PaymentModel


@pytest.fixture
def second_authenticated_client(client: TestClient) -> Generator[TestClient]:
    """A second `TestClient`, authenticated as an independent second
    workshop. Mirrors `test_payments_api.second_authenticated_client`.
    """
    with TestClient(app) as second_client:
        response = second_client.post(
            "/api/auth/register",
            json={
                "workshop_name": "Taller Rival Caja",
                "owner_name": "Otra Persona",
                "phone": "97712233",
                "password": "another-strong-password",
            },
        )
        assert response.status_code == 201
        yield second_client


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


def _payable_order(client: TestClient, *, unit_price_cents: int = 100000) -> dict:
    """An order approved with one labor line, so it accepts payments
    (`PAYABLE` includes `approved`). Mirrors
    `test_payments_api._payable_order`.
    """
    customer = _create_customer(client)
    vehicle = _create_vehicle(client, customer_id=customer["id"])
    order = client.post(
        "/api/work-orders", json={"id": str(uuid.uuid4()), "vehicle_id": vehicle["id"]}
    )
    assert order.status_code == 201, order.text
    order_id = order.json()["id"]
    line = client.post(
        f"/api/work-orders/{order_id}/lines",
        json={
            "id": str(uuid.uuid4()),
            "kind": "labor",
            "description": "Cambio de aceite",
            "quantity": 1,
            "unit_price_cents": unit_price_cents,
        },
    )
    assert line.status_code in (200, 201), line.text
    approved = client.put(f"/api/work-orders/{order_id}/status", json={"status": "approved"})
    assert approved.status_code == 200, approved.text
    return approved.json()


def _pay(client: TestClient, order_id: str, *, amount_cents: int, method: str = "cash") -> dict:
    response = client.post(
        f"/api/work-orders/{order_id}/payments",
        json={"id": str(uuid.uuid4()), "amount_cents": amount_cents, "method": method},
    )
    assert response.status_code == 201, response.text
    return response.json()["payments"][-1]


def _void(client: TestClient, order_id: str, payment_id: str) -> None:
    response = client.post(
        f"/api/work-orders/{order_id}/payments/{payment_id}/void",
        json={"reason": "duplicado"},
    )
    assert response.status_code == 200, response.text


def _backdate_payment(db_session: Session, payment_id: str, paid_at: datetime) -> None:
    """Directly rewrite a payment's `paid_at`.

    `record_payment` always stamps the real clock (`datetime.now(UTC)`),
    so this is the only way to place a payment at an exact instant near a
    day boundary. `db_session` is the same session the `TestClient`'s
    routes use (per `conftest.client`), so the write is visible to the
    next request in the same test.
    """
    db_session.execute(
        update(PaymentModel).where(PaymentModel.id == uuid.UUID(payment_id)).values(paid_at=paid_at)
    )
    db_session.commit()


def _summary(client: TestClient, *, date: str) -> dict:
    response = client.get("/api/cash-summary", params={"date": date})
    assert response.status_code == 200, response.text
    return response.json()


def test_a_payment_just_before_local_midnight_is_bucketed_into_the_earlier_day(
    authenticated_client: TestClient, db_session: Session
) -> None:
    order = _payable_order(authenticated_client)
    payment = _pay(authenticated_client, order["id"], amount_cents=10000)
    # 2026-10-07T05:59:00Z == 2026-10-06T23:59:00 in America/Tegucigalpa.
    _backdate_payment(db_session, payment["id"], datetime(2026, 10, 7, 5, 59, tzinfo=UTC))

    earlier_day = _summary(authenticated_client, date="2026-10-06")
    later_day = _summary(authenticated_client, date="2026-10-07")

    assert earlier_day["total_cents"] == 10000
    assert later_day["total_cents"] == 0


def test_a_payment_just_after_local_midnight_is_bucketed_into_the_next_day(
    authenticated_client: TestClient, db_session: Session
) -> None:
    order = _payable_order(authenticated_client)
    payment = _pay(authenticated_client, order["id"], amount_cents=10000)
    # 2026-10-07T06:01:00Z == 2026-10-07T00:01:00 in America/Tegucigalpa.
    _backdate_payment(db_session, payment["id"], datetime(2026, 10, 7, 6, 1, tzinfo=UTC))

    earlier_day = _summary(authenticated_client, date="2026-10-06")
    later_day = _summary(authenticated_client, date="2026-10-07")

    assert earlier_day["total_cents"] == 0
    assert later_day["total_cents"] == 10000


def test_mixed_method_totals_always_report_all_four_methods(
    authenticated_client: TestClient, db_session: Session
) -> None:
    order = _payable_order(authenticated_client, unit_price_cents=100000)
    cash = _pay(authenticated_client, order["id"], amount_cents=30000, method="cash")
    transfer = _pay(authenticated_client, order["id"], amount_cents=15000, method="transfer")
    card = _pay(authenticated_client, order["id"], amount_cents=5000, method="card")
    same_day = datetime(2026, 10, 6, 15, 0, tzinfo=UTC)
    for payment in (cash, transfer, card):
        _backdate_payment(db_session, payment["id"], same_day)

    summary = _summary(authenticated_client, date="2026-10-06")

    assert summary["totals_cents"] == {"cash": 30000, "transfer": 15000, "card": 5000, "other": 0}
    assert summary["total_cents"] == 50000


def test_only_the_requesting_workshops_payments_contribute(
    authenticated_client: TestClient,
    second_authenticated_client: TestClient,
    db_session: Session,
) -> None:
    foreign_order = _payable_order(second_authenticated_client)
    foreign_payment = _pay(second_authenticated_client, foreign_order["id"], amount_cents=99999)
    _backdate_payment(db_session, foreign_payment["id"], datetime(2026, 10, 6, 15, 0, tzinfo=UTC))

    summary = _summary(authenticated_client, date="2026-10-06")

    assert summary["total_cents"] == 0
    assert summary["payments"] == []


def test_a_voided_payment_does_not_contribute_to_the_summary(
    authenticated_client: TestClient, db_session: Session
) -> None:
    order = _payable_order(authenticated_client)
    payment = _pay(authenticated_client, order["id"], amount_cents=20000, method="cash")
    _backdate_payment(db_session, payment["id"], datetime(2026, 10, 6, 15, 0, tzinfo=UTC))
    _void(authenticated_client, order["id"], payment["id"])

    summary = _summary(authenticated_client, date="2026-10-06")

    assert summary["totals_cents"]["cash"] == 0
    assert summary["total_cents"] == 0
    assert summary["payments"] == []


def test_a_malformed_date_query_parameter_is_rejected(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/api/cash-summary", params={"date": "not-a-date"})

    assert response.status_code == 422

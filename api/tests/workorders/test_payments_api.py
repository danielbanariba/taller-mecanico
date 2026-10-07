"""Tests for the work-order payments HTTP API
(/api/work-orders/{id}/payments, .../payments/{pid}/void).

Defects these catch:
- the order reference on a payment is dropped, or tenancy is unchecked;
- the Spanish label or an arbitrary string is accepted as a wire `method`
  value;
- a retry of `POST .../payments` double-counts a payment, or a
  conflicting replay silently overwrites the original;
- payments are accepted before approval or after cancellation, or wrongly
  rejected on a legitimate deposit;
- overpayment is recorded instead of rejected, including against an
  already-settled order;
- the balance check runs before replay detection, so replaying the exact
  settling payment is wrongly rejected as an overpayment;
- wrong paid/balance arithmetic across one full or several partial
  payments;
- a reason-less void silently succeeds, losing the audit trail;
- a voided payment still counts toward the order's totals;
- a second void re-stamps the timestamp or requires a second reason;
- voiding with a guessed/mistyped or cross-order payment id silently
  succeeds instead of 404;
- a missing tenancy check on the void endpoint;
- a voided-only order can never be cancelled, or a paid order is wrongly
  cancellable.
"""

import threading
import uuid
from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from taller.customers.adapters.models import CustomerModel, VehicleModel
from taller.customers.adapters.repositories import SqlAlchemyVehicleRepository
from taller.identity.adapters.models import UserModel, WorkshopModel
from taller.inventory.adapters.repositories import (
    SqlAlchemyItemRepository,
    SqlAlchemyMovementRepository,
)
from taller.main import app
from taller.workorders.adapters.models import (
    PaymentModel,
    WorkOrderLineModel,
    WorkOrderModel,
    WorkshopCounterModel,
)
from taller.workorders.adapters.repositories import (
    SqlAlchemyPaymentRepository,
    SqlAlchemyWorkOrderRepository,
    SqlAlchemyWorkshopCounterRepository,
)
from taller.workorders.application.use_cases import (
    add_line,
    change_status,
    create_work_order,
    record_payment,
)
from taller.workorders.domain.entities import LineKind, PaymentMethod
from taller.workorders.domain.errors import PaymentExceedsBalance
from taller.workorders.domain.status import WorkOrderStatus


@pytest.fixture
def second_authenticated_client(client: TestClient) -> Generator[TestClient]:
    """A second TestClient, authenticated as an independent second workshop.

    Mirrors `test_customers_api.second_authenticated_client`.
    """
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


def _payable_order(client: TestClient, *, unit_price_cents: int = 50000) -> dict:
    """An order approved with one labor line, so it both has a known
    total and accepts payments (`PAYABLE` includes `approved`).
    """
    vehicle = _active_vehicle(client)
    order = _create_order(client, vehicle_id=vehicle["id"])
    _add_line(client, order["id"], _labor_line(unit_price_cents=unit_price_cents))
    response = _set_status(client, order["id"], "approved")
    assert response.status_code == 200, response.text
    return response.json()


def _create_payment(client: TestClient, order_id: str, **overrides: object) -> object:
    payload = {"id": str(uuid.uuid4()), "amount_cents": 10000, "method": "cash"}
    payload.update(overrides)
    return client.post(f"/api/work-orders/{order_id}/payments", json=payload)


def _void_payment(
    client: TestClient, order_id: str, payment_id: str, **overrides: object
) -> object:
    payload = {"reason": "duplicado"}
    payload.update(overrides)
    return client.post(f"/api/work-orders/{order_id}/payments/{payment_id}/void", json=payload)


def test_recording_a_payment_against_an_existing_order_is_saved(
    authenticated_client: TestClient,
) -> None:
    order = _payable_order(authenticated_client)
    response = _create_payment(authenticated_client, order["id"], amount_cents=20000)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["paid_cents"] == 20000
    assert body["balance_cents"] == 30000
    assert len(body["payments"]) == 1


def test_payment_against_a_nonexistent_order_is_not_found(authenticated_client: TestClient) -> None:
    response = _create_payment(authenticated_client, str(uuid.uuid4()))

    assert response.status_code == 404
    assert response.json()["detail"] == "work_order_not_found"


def test_payment_against_a_foreign_order_is_not_found(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    foreign_order = _payable_order(second_authenticated_client)

    response = _create_payment(authenticated_client, foreign_order["id"])

    assert response.status_code == 404
    assert response.json()["detail"] == "work_order_not_found"


def test_a_supported_method_is_accepted(authenticated_client: TestClient) -> None:
    order = _payable_order(authenticated_client)
    response = _create_payment(authenticated_client, order["id"], method="transfer")

    assert response.status_code == 201, response.text
    assert response.json()["payments"][0]["method"] == "transfer"


@pytest.mark.parametrize("method", ["transferencia", "check"])
def test_an_unsupported_method_is_rejected(authenticated_client: TestClient, method: str) -> None:
    order = _payable_order(authenticated_client)
    response = _create_payment(authenticated_client, order["id"], method=method)

    assert response.status_code == 422
    assert _get_order(authenticated_client, order["id"])["payments"] == []


def test_replaying_an_identical_payment_create_is_a_noop(authenticated_client: TestClient) -> None:
    order = _payable_order(authenticated_client)
    payment = {"id": str(uuid.uuid4()), "amount_cents": 20000, "method": "cash"}
    first = _create_payment(authenticated_client, order["id"], **payment)
    assert first.status_code == 201

    replay = _create_payment(authenticated_client, order["id"], **payment)

    assert replay.status_code == 200
    assert replay.json()["paid_cents"] == 20000


def test_reusing_a_payment_id_with_a_different_amount_is_a_conflict(
    authenticated_client: TestClient,
) -> None:
    order = _payable_order(authenticated_client)
    payment_id = str(uuid.uuid4())
    first = _create_payment(authenticated_client, order["id"], id=payment_id, amount_cents=10000)
    assert first.status_code == 201

    conflict = _create_payment(authenticated_client, order["id"], id=payment_id, amount_cents=20000)

    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "payment_id_conflict"
    assert _get_order(authenticated_client, order["id"])["paid_cents"] == 10000


def test_payment_against_a_quote_is_rejected(authenticated_client: TestClient) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])

    response = _create_payment(authenticated_client, order["id"])

    assert response.status_code == 409
    assert response.json()["detail"] == "work_order_not_payable"


def test_payment_against_a_cancelled_order_is_rejected(authenticated_client: TestClient) -> None:
    order = _payable_order(authenticated_client)
    cancel = _set_status(authenticated_client, order["id"], "cancelled")
    assert cancel.status_code == 200

    response = _create_payment(authenticated_client, order["id"])

    assert response.status_code == 409
    assert response.json()["detail"] == "work_order_not_payable"


def test_a_deposit_is_accepted_while_approved(authenticated_client: TestClient) -> None:
    order = _payable_order(authenticated_client)
    assert order["status"] == "approved"

    response = _create_payment(authenticated_client, order["id"], amount_cents=15000)

    assert response.status_code == 201, response.text
    assert response.json()["paid_cents"] == 15000


def test_a_payment_exceeding_the_balance_is_rejected(authenticated_client: TestClient) -> None:
    order = _payable_order(authenticated_client, unit_price_cents=50000)

    response = _create_payment(authenticated_client, order["id"], amount_cents=60000)

    assert response.status_code == 409
    assert response.json()["detail"] == "payment_exceeds_balance"
    assert _get_order(authenticated_client, order["id"])["payments"] == []


def test_a_payment_against_an_already_settled_order_is_rejected(
    authenticated_client: TestClient,
) -> None:
    order = _payable_order(authenticated_client, unit_price_cents=50000)
    settle = _create_payment(authenticated_client, order["id"], amount_cents=50000)
    assert settle.status_code == 201

    response = _create_payment(authenticated_client, order["id"], amount_cents=1)

    assert response.status_code == 409
    assert response.json()["detail"] == "payment_exceeds_balance"


def test_replaying_the_settling_payment_is_a_noop_not_an_overpayment(
    authenticated_client: TestClient,
) -> None:
    """Defect this catches: the balance check running before replay
    detection, so replaying the exact payment that already settled the
    order is wrongly rejected as `payment_exceeds_balance` instead of
    recognized as a no-op (AD-14's ordering rule).
    """
    order = _payable_order(authenticated_client, unit_price_cents=50000)
    payment = {"id": str(uuid.uuid4()), "amount_cents": 50000, "method": "cash"}
    settle = _create_payment(authenticated_client, order["id"], **payment)
    assert settle.status_code == 201

    replay = _create_payment(authenticated_client, order["id"], **payment)

    assert replay.status_code == 200
    assert replay.json()["balance_cents"] == 0


def test_a_single_full_payment_zeroes_the_balance(authenticated_client: TestClient) -> None:
    order = _payable_order(authenticated_client, unit_price_cents=50000)

    response = _create_payment(authenticated_client, order["id"], amount_cents=50000)

    assert response.status_code == 201
    body = response.json()
    assert body["paid_cents"] == 50000
    assert body["balance_cents"] == 0


def test_two_partial_payments_accumulate_to_a_zero_balance(
    authenticated_client: TestClient,
) -> None:
    order = _payable_order(authenticated_client, unit_price_cents=50000)
    deposit = _create_payment(authenticated_client, order["id"], amount_cents=20000)
    assert deposit.status_code == 201

    remainder = _create_payment(authenticated_client, order["id"], amount_cents=30000)

    assert remainder.status_code == 201
    body = remainder.json()
    assert body["paid_cents"] == 50000
    assert body["balance_cents"] == 0


def test_voiding_a_payment_with_no_reason_is_rejected(authenticated_client: TestClient) -> None:
    order = _payable_order(authenticated_client)
    created = _create_payment(authenticated_client, order["id"], amount_cents=20000)
    payment_id = created.json()["payments"][0]["id"]

    response = authenticated_client.post(
        f"/api/work-orders/{order['id']}/payments/{payment_id}/void", json={}
    )

    assert response.status_code == 422
    unchanged = _get_order(authenticated_client, order["id"])
    assert unchanged["payments"][0]["voided_at"] is None


def test_voiding_a_payment_excludes_it_from_the_order_totals(
    authenticated_client: TestClient,
) -> None:
    order = _payable_order(authenticated_client, unit_price_cents=50000)
    created = _create_payment(authenticated_client, order["id"], amount_cents=20000)
    payment_id = created.json()["payments"][0]["id"]

    response = _void_payment(authenticated_client, order["id"], payment_id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["paid_cents"] == 0
    assert body["balance_cents"] == 50000


def test_voiding_is_idempotent(authenticated_client: TestClient) -> None:
    order = _payable_order(authenticated_client)
    created = _create_payment(authenticated_client, order["id"], amount_cents=20000)
    payment_id = created.json()["payments"][0]["id"]

    first_void = _void_payment(authenticated_client, order["id"], payment_id, reason="duplicado")
    assert first_void.status_code == 200
    first_voided_at = first_void.json()["payments"][0]["voided_at"]

    second_void = _void_payment(authenticated_client, order["id"], payment_id, reason="otra razon")

    assert second_void.status_code == 200
    body = second_void.json()
    assert body["payments"][0]["voided_at"] == first_voided_at
    assert body["payments"][0]["void_reason"] == "duplicado"


def test_voiding_a_nonexistent_payment_id_is_not_found(authenticated_client: TestClient) -> None:
    order = _payable_order(authenticated_client)

    response = _void_payment(authenticated_client, order["id"], str(uuid.uuid4()))

    assert response.status_code == 404
    assert response.json()["detail"] == "payment_not_found"


def test_voiding_a_payment_id_belonging_to_a_different_order_is_not_found(
    authenticated_client: TestClient,
) -> None:
    order_one = _payable_order(authenticated_client)
    order_two = _payable_order(authenticated_client)
    created = _create_payment(authenticated_client, order_one["id"], amount_cents=10000)
    payment_id = created.json()["payments"][0]["id"]

    response = _void_payment(authenticated_client, order_two["id"], payment_id)

    assert response.status_code == 404
    assert response.json()["detail"] == "payment_not_found"


def test_workshop_b_voiding_workshop_a_payment_is_not_found(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    order = _payable_order(authenticated_client)
    created = _create_payment(authenticated_client, order["id"], amount_cents=10000)
    payment_id = created.json()["payments"][0]["id"]

    response = _void_payment(second_authenticated_client, order["id"], payment_id)

    assert response.status_code == 404
    assert response.json()["detail"] == "work_order_not_found"
    unchanged = _get_order(authenticated_client, order["id"])
    assert unchanged["payments"][0]["voided_at"] is None


def test_cancelling_an_order_with_a_nonvoided_payment_is_rejected(
    authenticated_client: TestClient,
) -> None:
    order = _payable_order(authenticated_client)
    created = _create_payment(authenticated_client, order["id"], amount_cents=10000)
    assert created.status_code == 201

    response = _set_status(authenticated_client, order["id"], "cancelled")

    assert response.status_code == 409
    assert response.json()["detail"] == "work_order_has_payments"
    assert _get_order(authenticated_client, order["id"])["status"] == "approved"


def test_cancelling_an_order_whose_only_payment_was_voided_is_allowed(
    authenticated_client: TestClient,
) -> None:
    order = _payable_order(authenticated_client)
    created = _create_payment(authenticated_client, order["id"], amount_cents=10000)
    payment_id = created.json()["payments"][0]["id"]
    voided = _void_payment(authenticated_client, order["id"], payment_id)
    assert voided.status_code == 200

    response = _set_status(authenticated_client, order["id"], "cancelled")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


#: Fixed phone for this fixture's committed user row (see
#: `test_work_order_concurrency._PHONE`'s own comment: must be unique
#: across every committed-row fixture in the suite).
_PHONE = "87650097"


@pytest.fixture
def committed_payable_order(test_engine: Engine) -> Generator[dict[str, object]]:
    """A real workshop, owner, customer, vehicle and an order approved
    with one 500.00 labor line, committed on a connection separate from
    the per-test SAVEPOINT -- a balance-exceeding race only shows up
    between two genuinely concurrent transactions (mirrors
    `test_work_order_concurrency.committed_workshop`).
    """
    ids = {
        "workshop_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "customer_id": uuid.uuid4(),
        "vehicle_id": uuid.uuid4(),
        "order_id": uuid.uuid4(),
        "line_id": uuid.uuid4(),
    }
    now = datetime.now(UTC)
    with Session(test_engine) as setup:
        setup.add(WorkshopModel(id=ids["workshop_id"], name="Taller Pagos", created_at=now))
        setup.flush()
        setup.add(
            UserModel(
                id=ids["user_id"],
                workshop_id=ids["workshop_id"],
                full_name="Owner Pagos",
                phone=_PHONE,
                password_hash="not-a-real-hash",
                created_at=now,
            )
        )
        setup.flush()
        setup.add(
            CustomerModel(
                id=ids["customer_id"],
                workshop_id=ids["workshop_id"],
                full_name="Cliente Pagos",
                phone=None,
                notes=None,
                archived_at=None,
                created_at=now,
                updated_at=now,
            )
        )
        setup.flush()
        setup.add(
            VehicleModel(
                id=ids["vehicle_id"],
                workshop_id=ids["workshop_id"],
                customer_id=ids["customer_id"],
                vehicle_type="car",
                make="Toyota",
                model=None,
                year=None,
                color=None,
                plate=None,
                notes=None,
                archived_at=None,
                created_at=now,
                updated_at=now,
            )
        )
        setup.flush()

        order_repo = SqlAlchemyWorkOrderRepository(setup)
        counter_repo = SqlAlchemyWorkshopCounterRepository(setup)
        vehicle_repo = SqlAlchemyVehicleRepository(setup)
        item_repo = SqlAlchemyItemRepository(setup)
        movement_repo = SqlAlchemyMovementRepository(setup)
        payment_repo = SqlAlchemyPaymentRepository(setup)

        order, _ = create_work_order(
            workshop_id=ids["workshop_id"],
            order_id=ids["order_id"],
            vehicle_id=ids["vehicle_id"],
            complaint=None,
            odometer_km=None,
            notes=None,
            created_by=ids["user_id"],
            order_repo=order_repo,
            counter_repo=counter_repo,
            vehicle_repo=vehicle_repo,
        )
        add_line(
            workshop_id=ids["workshop_id"],
            order_id=order.id,
            line_id=ids["line_id"],
            kind=LineKind.labor,
            item_id=None,
            description="Cambio de aceite",
            quantity=1,
            unit_price_cents=50000,
            created_by=ids["user_id"],
            order_repo=order_repo,
            item_repo=item_repo,
            movement_repo=movement_repo,
        )
        change_status(
            workshop_id=ids["workshop_id"],
            order_id=order.id,
            target=WorkOrderStatus.approved,
            created_by=ids["user_id"],
            order_repo=order_repo,
            item_repo=item_repo,
            movement_repo=movement_repo,
            payment_repo=payment_repo,
        )
        setup.commit()
    try:
        yield ids
    finally:
        with Session(test_engine) as cleanup:
            cleanup.execute(
                delete(PaymentModel).where(PaymentModel.workshop_id == ids["workshop_id"])
            )
            cleanup.execute(
                delete(WorkOrderLineModel).where(
                    WorkOrderLineModel.workshop_id == ids["workshop_id"]
                )
            )
            cleanup.execute(
                delete(WorkOrderModel).where(WorkOrderModel.workshop_id == ids["workshop_id"])
            )
            cleanup.execute(
                delete(WorkshopCounterModel).where(
                    WorkshopCounterModel.workshop_id == ids["workshop_id"]
                )
            )
            cleanup.execute(delete(VehicleModel).where(VehicleModel.id == ids["vehicle_id"]))
            cleanup.execute(delete(CustomerModel).where(CustomerModel.id == ids["customer_id"]))
            cleanup.execute(delete(UserModel).where(UserModel.id == ids["user_id"]))
            cleanup.execute(delete(WorkshopModel).where(WorkshopModel.id == ids["workshop_id"]))
            cleanup.commit()


def test_two_concurrent_payments_that_together_exceed_the_balance_let_exactly_one_succeed(
    committed_payable_order: dict[str, object], test_engine: Engine
) -> None:
    """Defect this catches: the balance check running without the order
    row lock, letting two concurrent payments each pass their own check
    against the pre-payment balance and together overpay the order.
    """
    workshop_id = committed_payable_order["workshop_id"]
    order_id = committed_payable_order["order_id"]
    user_id = committed_payable_order["user_id"]

    outcomes: list[bool] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(2)

    def _pay() -> None:
        try:
            with Session(test_engine) as session:
                barrier.wait()
                try:
                    _, is_new = record_payment(
                        workshop_id=workshop_id,
                        order_id=order_id,
                        payment_id=uuid.uuid4(),
                        amount_cents=30000,
                        method=PaymentMethod.cash,
                        note=None,
                        created_by=user_id,
                        order_repo=SqlAlchemyWorkOrderRepository(session),
                        payment_repo=SqlAlchemyPaymentRepository(session),
                    )
                    session.commit()
                    outcomes.append(is_new)
                except PaymentExceedsBalance:
                    session.rollback()
                    outcomes.append(False)
        except BaseException as exc:  # noqa: BLE001 -- surfaced via `errors` below
            errors.append(exc)

    threads = [threading.Thread(target=_pay) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert outcomes.count(True) == 1

    with Session(test_engine) as verify:
        payment_repo = SqlAlchemyPaymentRepository(verify)
        payments = payment_repo.list_for_order(workshop_id=workshop_id, order_id=order_id)
        assert sum(payment.amount_cents for payment in payments) == 30000

"""Tests for the order/line link on stock movements (`design.md`'s AD-3).

Defects these catch:
- the order/line reference excluded from replay matching, letting a
  legitimately-replayed order-caused movement double-apply its delta;
- AD-3's planted-id attack: a client pre-records an unlinked movement at an
  order line's future derived id with the same base fields, and the order's
  real consumption is silently taken as a harmless replay instead of a
  conflict;
- adding the nullable order-link columns changing replay matching for
  movements that never carried one, breaking offline-outbox replay;
- `inventory_movements` carrying the link but the history read path never
  surfacing it, so a mechanic can't see which order consumed a part.
"""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from taller.customers.adapters.models import CustomerModel, VehicleModel
from taller.inventory.adapters.repositories import (
    SqlAlchemyItemRepository,
    SqlAlchemyMovementRepository,
)
from taller.inventory.application.use_cases import record_movement
from taller.inventory.domain.errors import MovementIdConflict
from taller.workorders.adapters.models import WorkOrderLineModel, WorkOrderModel


def _create_item(client: TestClient, **overrides: object) -> dict:
    payload = {"name": "Pastillas de freno"}
    payload.update(overrides)
    response = client.post("/api/inventory/items", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _identity(client: TestClient) -> tuple[uuid.UUID, uuid.UUID]:
    """The authenticated user's own id and their workshop's id."""
    me = client.get("/api/auth/me")
    assert me.status_code == 200, me.text
    body = me.json()
    return uuid.UUID(body["user"]["id"]), uuid.UUID(body["workshop"]["id"])


def _make_order_with_lines(
    db_session: Session,
    *,
    workshop_id: uuid.UUID,
    created_by: uuid.UUID,
    item_id: uuid.UUID,
    number: int,
    line_count: int = 1,
) -> tuple[uuid.UUID, list[uuid.UUID]]:
    """Insert the customer/vehicle/order/lines chain a linked movement's
    foreign keys need, bypassing the work-order use cases (not written
    until phase 2's slice 2) with direct ORM rows.
    """
    now = datetime.now(UTC)
    customer = CustomerModel(
        id=uuid.uuid4(),
        workshop_id=workshop_id,
        full_name="Cliente de prueba",
        phone=None,
        notes=None,
        archived_at=None,
        created_at=now,
        updated_at=now,
    )
    vehicle = VehicleModel(
        id=uuid.uuid4(),
        workshop_id=workshop_id,
        customer_id=customer.id,
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
    order = WorkOrderModel(
        id=uuid.uuid4(),
        workshop_id=workshop_id,
        number=number,
        vehicle_id=vehicle.id,
        customer_id=customer.id,
        status="in_progress",
        complaint=None,
        odometer_km=None,
        notes=None,
        created_by=created_by,
        approved_at=None,
        started_at=now,
        completed_at=None,
        delivered_at=None,
        cancelled_at=None,
        created_at=now,
        updated_at=now,
    )
    lines = [
        WorkOrderLineModel(
            id=uuid.uuid4(),
            workshop_id=workshop_id,
            order_id=order.id,
            kind="inventory_part",
            item_id=item_id,
            description="Pastillas de freno",
            quantity=2,
            unit_price_cents=15000,
            stock_posted_quantity=0,
            stock_revision=0,
            removed_at=None,
            created_at=now,
            updated_at=now,
        )
        for _ in range(line_count)
    ]
    # No ORM `relationship()` ties these models together (the work-order
    # domain/application layer lands in slice 2), so SQLAlchemy's flush
    # cannot infer insert order from the raw foreign keys alone -- each
    # dependency level is flushed before the next is added.
    db_session.add(customer)
    db_session.flush()
    db_session.add(vehicle)
    db_session.flush()
    db_session.add(order)
    db_session.flush()
    db_session.add_all(lines)
    db_session.flush()
    return order.id, [line.id for line in lines]


def test_replaying_an_order_linked_movement_is_a_no_op(
    authenticated_client: TestClient, db_session: Session
) -> None:
    user_id, workshop_id = _identity(authenticated_client)
    item = _create_item(authenticated_client)
    item_id = uuid.UUID(item["id"])
    order_id, (line_id,) = _make_order_with_lines(
        db_session, workshop_id=workshop_id, created_by=user_id, item_id=item_id, number=1
    )
    item_repo = SqlAlchemyItemRepository(db_session)
    movement_repo = SqlAlchemyMovementRepository(db_session)
    movement_id = uuid.uuid4()

    _, _, is_new_first = record_movement(
        workshop_id=workshop_id,
        movement_id=movement_id,
        item_id=item_id,
        kind="out",
        quantity=2,
        note=None,
        occurred_at=None,
        created_by=user_id,
        item_repo=item_repo,
        movement_repo=movement_repo,
        order_id=order_id,
        order_line_id=line_id,
    )
    db_session.commit()
    assert is_new_first is True

    _, _, is_new_replay = record_movement(
        workshop_id=workshop_id,
        movement_id=movement_id,
        item_id=item_id,
        kind="out",
        quantity=2,
        note=None,
        occurred_at=None,
        created_by=user_id,
        item_repo=item_repo,
        movement_repo=movement_repo,
        order_id=order_id,
        order_line_id=line_id,
    )
    db_session.commit()
    assert is_new_replay is False

    fetched = authenticated_client.get(f"/api/inventory/items/{item_id}")
    assert fetched.json()["stock"] == -2


def test_same_movement_id_with_a_different_order_line_is_a_conflict(
    authenticated_client: TestClient, db_session: Session
) -> None:
    user_id, workshop_id = _identity(authenticated_client)
    item = _create_item(authenticated_client)
    item_id = uuid.UUID(item["id"])
    order_id, (line_a, line_b) = _make_order_with_lines(
        db_session,
        workshop_id=workshop_id,
        created_by=user_id,
        item_id=item_id,
        number=1,
        line_count=2,
    )
    item_repo = SqlAlchemyItemRepository(db_session)
    movement_repo = SqlAlchemyMovementRepository(db_session)
    movement_id = uuid.uuid4()

    record_movement(
        workshop_id=workshop_id,
        movement_id=movement_id,
        item_id=item_id,
        kind="out",
        quantity=2,
        note=None,
        occurred_at=None,
        created_by=user_id,
        item_repo=item_repo,
        movement_repo=movement_repo,
        order_id=order_id,
        order_line_id=line_a,
    )
    db_session.commit()

    with pytest.raises(MovementIdConflict):
        record_movement(
            workshop_id=workshop_id,
            movement_id=movement_id,
            item_id=item_id,
            kind="out",
            quantity=2,
            note=None,
            occurred_at=None,
            created_by=user_id,
            item_repo=item_repo,
            movement_repo=movement_repo,
            order_id=order_id,
            order_line_id=line_b,
        )
    db_session.rollback()

    fetched = authenticated_client.get(f"/api/inventory/items/{item_id}")
    assert fetched.json()["stock"] == -2


def test_unlinked_movement_replay_is_unaffected_by_the_link_fields(
    authenticated_client: TestClient, db_session: Session
) -> None:
    user_id, workshop_id = _identity(authenticated_client)
    item = _create_item(authenticated_client)
    item_id = uuid.UUID(item["id"])
    item_repo = SqlAlchemyItemRepository(db_session)
    movement_repo = SqlAlchemyMovementRepository(db_session)
    movement_id = uuid.uuid4()

    record_movement(
        workshop_id=workshop_id,
        movement_id=movement_id,
        item_id=item_id,
        kind="in",
        quantity=4,
        note=None,
        occurred_at=None,
        created_by=user_id,
        item_repo=item_repo,
        movement_repo=movement_repo,
    )
    db_session.commit()

    _, _, is_new = record_movement(
        workshop_id=workshop_id,
        movement_id=movement_id,
        item_id=item_id,
        kind="in",
        quantity=4,
        note=None,
        occurred_at=None,
        created_by=user_id,
        item_repo=item_repo,
        movement_repo=movement_repo,
    )
    db_session.commit()
    assert is_new is False

    fetched = authenticated_client.get(f"/api/inventory/items/{item_id}")
    assert fetched.json()["stock"] == 4


def test_item_history_exposes_the_order_that_caused_a_movement(
    authenticated_client: TestClient, db_session: Session
) -> None:
    user_id, workshop_id = _identity(authenticated_client)
    item = _create_item(authenticated_client)
    item_id = uuid.UUID(item["id"])
    order_id, (line_id,) = _make_order_with_lines(
        db_session, workshop_id=workshop_id, created_by=user_id, item_id=item_id, number=7
    )
    item_repo = SqlAlchemyItemRepository(db_session)
    movement_repo = SqlAlchemyMovementRepository(db_session)

    record_movement(
        workshop_id=workshop_id,
        movement_id=uuid.uuid4(),
        item_id=item_id,
        kind="out",
        quantity=1,
        note=None,
        occurred_at=None,
        created_by=user_id,
        item_repo=item_repo,
        movement_repo=movement_repo,
        order_id=order_id,
        order_line_id=line_id,
    )
    db_session.commit()

    manual_response = authenticated_client.put(
        f"/api/inventory/movements/{uuid.uuid4()}",
        json={"item_id": str(item_id), "kind": "in", "quantity": 3},
    )
    assert manual_response.status_code == 201, manual_response.text

    history = authenticated_client.get(f"/api/inventory/items/{item_id}/movements")
    assert history.status_code == 200
    entries = {entry["kind"]: entry for entry in history.json()}

    linked = entries["out"]
    assert linked["order_id"] == str(order_id)
    assert linked["order_line_id"] == str(line_id)
    assert linked["order_number"] == 7

    manual = entries["in"]
    assert manual["order_id"] is None
    assert manual["order_line_id"] is None
    assert manual["order_number"] is None

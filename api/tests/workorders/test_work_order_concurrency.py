"""Concurrency tests for work-order numbering (`create_work_order`).

Uses two real connections and real threads, unlike the rest of the suite
(one connection per test, inside a rolled-back SAVEPOINT): a numbering race
only shows up between two genuinely concurrent transactions. The workshop,
user, customer and vehicle this needs are committed on a separate
connection, the same way `test_login_throttle_repository.py`'s
`committed_throttle_row` commits the row its own lock test needs; this
fixture deletes everything it inserted on the way out.
"""

import threading
import uuid
from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from taller.customers.adapters.models import CustomerModel, VehicleModel
from taller.customers.adapters.repositories import SqlAlchemyVehicleRepository
from taller.identity.adapters.models import UserModel, WorkshopModel
from taller.workorders.adapters.models import WorkOrderModel, WorkshopCounterModel
from taller.workorders.adapters.repositories import (
    SqlAlchemyWorkOrderRepository,
    SqlAlchemyWorkshopCounterRepository,
)
from taller.workorders.application.use_cases import create_work_order

#: Fixed phone for this fixture's committed user row (must be unique,
#: 8 digits, and unused by any other test's committed data).
_PHONE = "87650099"


@pytest.fixture
def committed_workshop(test_engine: Engine) -> Generator[dict[str, uuid.UUID]]:
    """A real workshop, owner user, customer and vehicle, committed on a
    connection separate from the per-test SAVEPOINT, so two independent
    `Session(test_engine)` connections can genuinely race against the same
    counter row and primary key the way two concurrent HTTP requests
    would.
    """
    ids = {
        "workshop_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "customer_id": uuid.uuid4(),
        "vehicle_id": uuid.uuid4(),
    }
    now = datetime.now(UTC)
    with Session(test_engine) as setup:
        # Flushed one dependency level at a time: SQLAlchemy's flush does
        # not auto-order inserts across unrelated mapped classes by raw
        # table-level FK alone when no ORM `relationship()` connects them
        # (the same gotcha P2.S1 hit composing a customer+vehicle+order in
        # one `add_all()`), so a single flush at the end can try to insert
        # `customers` before `workshops` exists.
        setup.add(WorkshopModel(id=ids["workshop_id"], name="Taller Concurrencia", created_at=now))
        setup.flush()
        setup.add(
            UserModel(
                id=ids["user_id"],
                workshop_id=ids["workshop_id"],
                full_name="Owner Concurrencia",
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
                full_name="Cliente Concurrencia",
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
        setup.commit()
    try:
        yield ids
    finally:
        with Session(test_engine) as cleanup:
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


def test_concurrent_creates_for_one_workshop_get_distinct_sequential_numbers(
    committed_workshop: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Defect this catches: a read-then-write numbering scheme racing under
    concurrent creates, assigning the same number to two orders or leaving
    a gap between them.
    """
    workshop_id = committed_workshop["workshop_id"]
    vehicle_id = committed_workshop["vehicle_id"]
    user_id = committed_workshop["user_id"]

    numbers: list[int] = []
    errors: list[BaseException] = []

    def _create() -> None:
        try:
            with Session(test_engine) as session:
                order, _ = create_work_order(
                    workshop_id=workshop_id,
                    order_id=uuid.uuid4(),
                    vehicle_id=vehicle_id,
                    complaint=None,
                    odometer_km=None,
                    notes=None,
                    created_by=user_id,
                    order_repo=SqlAlchemyWorkOrderRepository(session),
                    counter_repo=SqlAlchemyWorkshopCounterRepository(session),
                    vehicle_repo=SqlAlchemyVehicleRepository(session),
                )
                session.commit()
                numbers.append(order.number)
        except BaseException as exc:  # noqa: BLE001 -- surfaced via `errors` below
            errors.append(exc)

    threads = [threading.Thread(target=_create) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert sorted(numbers) == [1, 2]


def test_concurrent_creates_with_the_same_id_persist_exactly_one_order(
    committed_workshop: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Defect this catches: a rolled-back duplicate insert (two concurrent
    creates racing on the same client id) leaves a gap in the numbering
    sequence instead of being retried cleanly, or persists two rows for one
    client id.
    """
    workshop_id = committed_workshop["workshop_id"]
    vehicle_id = committed_workshop["vehicle_id"]
    user_id = committed_workshop["user_id"]
    order_id = uuid.uuid4()
    barrier = threading.Barrier(2)

    outcomes: list[bool] = []
    errors: list[BaseException] = []

    def _create_once(session: Session) -> tuple[object, bool]:
        return create_work_order(
            workshop_id=workshop_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            complaint=None,
            odometer_km=None,
            notes=None,
            created_by=user_id,
            order_repo=SqlAlchemyWorkOrderRepository(session),
            counter_repo=SqlAlchemyWorkshopCounterRepository(session),
            vehicle_repo=SqlAlchemyVehicleRepository(session),
        )

    def _create_with_retry() -> None:
        try:
            with Session(test_engine) as session:
                barrier.wait()
                try:
                    _, is_new = _create_once(session)
                    session.commit()
                except IntegrityError:
                    # Mirrors the router's own retry-once-on-IntegrityError
                    # dance (design.md's AD-6): the rollback below undoes
                    # this attempt's counter bump, so the retry's
                    # replay-check finds the row the other thread just
                    # committed and never burns a second number.
                    session.rollback()
                    _, is_new = _create_once(session)
                    session.commit()
                outcomes.append(is_new)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_create_with_retry) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert sorted(outcomes) == [False, True]

    with Session(test_engine) as verify:
        rows = (
            verify.query(WorkOrderModel)
            .filter(WorkOrderModel.workshop_id == workshop_id, WorkOrderModel.id == order_id)
            .all()
        )
        assert len(rows) == 1

        counter = verify.get(WorkshopCounterModel, (workshop_id, "work_order"))
        assert counter is not None
        assert counter.value == 1

"""Concurrency tests for work-order numbering (`create_work_order`) and
stock-consuming status transitions (`change_status`).

Uses two real connections and real threads, unlike the rest of the suite
(one connection per test, inside a rolled-back SAVEPOINT): a numbering or
locking race only shows up between two genuinely concurrent transactions.
The workshop, user, customer and vehicle this needs are committed on a
separate connection, the same way `test_login_throttle_repository.py`'s
`committed_throttle_row` commits the row its own lock test needs; each
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
from taller.inventory.adapters.models import ItemModel, StockMovementModel
from taller.inventory.adapters.repositories import (
    SqlAlchemyItemRepository,
    SqlAlchemyMovementRepository,
)
from taller.workorders.adapters.models import (
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
    update_work_order,
)
from taller.workorders.domain.entities import LineKind
from taller.workorders.domain.status import WorkOrderStatus

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


class _ReadPausingWorkOrderRepository:
    """Wraps the real repository so a test can land a concurrent commit
    precisely between `update_work_order`'s own (unlocked) read and its
    later `save()` -- the exact window a missing row lock leaves open.
    `get_for_update` is a plain passthrough: once `update_work_order` is
    fixed to call it instead of `get_by_id`, it blocks on the real
    Postgres row lock on its own, and this wrapper's pause never engages.
    """

    def __init__(
        self,
        inner: SqlAlchemyWorkOrderRepository,
        read_done: threading.Event,
        resume: threading.Event,
    ) -> None:
        self._inner = inner
        self._read_done = read_done
        self._resume = resume

    def get_by_id(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID):
        order = self._inner.get_by_id(workshop_id=workshop_id, order_id=order_id)
        self._read_done.set()
        self._resume.wait(timeout=5)
        return order

    def get_for_update(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID):
        return self._inner.get_for_update(workshop_id=workshop_id, order_id=order_id)

    def save(self, order) -> None:
        self._inner.save(order)


def test_update_work_order_does_not_revert_a_concurrently_committed_status_change(
    committed_workshop: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Defect this catches: `update_work_order` (the order's own PATCH --
    editing `complaint`/`odometer_km`/`notes`) reads the order without
    taking its row lock, then its `save()` blindly rewrites every column
    (including `status`) from that stale snapshot. If a `change_status`
    call locks the row, commits a transition, and releases the lock
    while the PATCH's own re-read inside `save()` lands right after that
    commit, the PATCH's stale status overwrites the just-committed one --
    `design.md`'s AD-5 requires every mutating work-order use case to
    lock the order row first, exactly to close this window.
    """
    workshop_id = committed_workshop["workshop_id"]
    vehicle_id = committed_workshop["vehicle_id"]
    user_id = committed_workshop["user_id"]

    with Session(test_engine) as setup_session:
        order, _ = create_work_order(
            workshop_id=workshop_id,
            order_id=uuid.uuid4(),
            vehicle_id=vehicle_id,
            complaint=None,
            odometer_km=None,
            notes=None,
            created_by=user_id,
            order_repo=SqlAlchemyWorkOrderRepository(setup_session),
            counter_repo=SqlAlchemyWorkshopCounterRepository(setup_session),
            vehicle_repo=SqlAlchemyVehicleRepository(setup_session),
        )
        setup_session.commit()
        order_id = order.id

    read_done = threading.Event()
    resume = threading.Event()
    errors: list[BaseException] = []

    def _patch() -> None:
        try:
            with Session(test_engine) as session:
                repo = _ReadPausingWorkOrderRepository(
                    SqlAlchemyWorkOrderRepository(session), read_done, resume
                )
                update_work_order(
                    workshop_id=workshop_id,
                    order_id=order_id,
                    fields={"notes": "Actualizado durante la aprobación"},
                    order_repo=repo,
                )
                session.commit()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    with Session(test_engine) as holder_session:
        # Lock the order row and transition it, exactly like a real
        # `PUT .../status` request would, but hold the transaction open
        # (no commit yet).
        change_status(
            workshop_id=workshop_id,
            order_id=order_id,
            target=WorkOrderStatus.approved,
            created_by=user_id,
            order_repo=SqlAlchemyWorkOrderRepository(holder_session),
            item_repo=SqlAlchemyItemRepository(holder_session),
            movement_repo=SqlAlchemyMovementRepository(holder_session),
            payment_repo=SqlAlchemyPaymentRepository(holder_session),
        )

        thread = threading.Thread(target=_patch)
        thread.start()
        # On the buggy (`get_by_id`) path, `read_done` fires almost
        # instantly, before this commit. On the fixed (`get_for_update`)
        # path, the PATCH blocks on the real row lock instead and never
        # reaches the wrapper's hook, so this just bounds the wait.
        read_done.wait(timeout=1)
        holder_session.commit()
        resume.set()

    thread.join(timeout=5)
    assert not errors, errors

    with Session(test_engine) as verify:
        model = verify.get(WorkOrderModel, order_id)
        assert model is not None
        assert model.status == WorkOrderStatus.approved.value
        assert model.notes == "Actualizado durante la aprobación"


#: Fixed phone for this fixture's committed user row (see `_PHONE`'s own
#: comment above: must be unique across every committed-row fixture).
_DEADLOCK_PHONE = "87650098"


@pytest.fixture
def committed_deadlock_orders(test_engine: Engine) -> Generator[dict[str, uuid.UUID]]:
    """Two approved orders for one workshop, each with inventory-part lines
    referencing the same two items in reverse order (`order_x`: `[A, B]`,
    `order_y`: `[B, A]`), committed on a connection separate from the
    per-test SAVEPOINT -- AD-5's deadlock-freedom claim only shows up
    between two genuinely concurrent transactions locking rows in the
    order each line declares them, instead of the sorted `(item_id,
    line_id)` order `plan_reconciliation` actually uses.
    """
    ids = {
        "workshop_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "customer_id": uuid.uuid4(),
        "vehicle_id": uuid.uuid4(),
        "item_a_id": uuid.uuid4(),
        "item_b_id": uuid.uuid4(),
        "order_x_id": uuid.uuid4(),
        "order_y_id": uuid.uuid4(),
    }
    now = datetime.now(UTC)
    with Session(test_engine) as setup:
        setup.add(WorkshopModel(id=ids["workshop_id"], name="Taller Deadlock", created_at=now))
        setup.flush()
        setup.add(
            UserModel(
                id=ids["user_id"],
                workshop_id=ids["workshop_id"],
                full_name="Owner Deadlock",
                phone=_DEADLOCK_PHONE,
                password_hash="not-a-real-hash",
                created_at=now,
            )
        )
        setup.flush()
        setup.add(
            CustomerModel(
                id=ids["customer_id"],
                workshop_id=ids["workshop_id"],
                full_name="Cliente Deadlock",
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
        setup.add(
            ItemModel(
                id=ids["item_a_id"],
                workshop_id=ids["workshop_id"],
                name="Pieza Deadlock A",
                category=None,
                unit="unidad",
                min_stock=0,
                sale_price_cents=None,
                notes=None,
                stock=10,
                archived_at=None,
                created_at=now,
                updated_at=now,
            )
        )
        setup.add(
            ItemModel(
                id=ids["item_b_id"],
                workshop_id=ids["workshop_id"],
                name="Pieza Deadlock B",
                category=None,
                unit="unidad",
                min_stock=0,
                sale_price_cents=None,
                notes=None,
                stock=10,
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

        order_x, _ = create_work_order(
            workshop_id=ids["workshop_id"],
            order_id=ids["order_x_id"],
            vehicle_id=ids["vehicle_id"],
            complaint=None,
            odometer_km=None,
            notes=None,
            created_by=ids["user_id"],
            order_repo=order_repo,
            counter_repo=counter_repo,
            vehicle_repo=vehicle_repo,
        )
        order_y, _ = create_work_order(
            workshop_id=ids["workshop_id"],
            order_id=ids["order_y_id"],
            vehicle_id=ids["vehicle_id"],
            complaint=None,
            odometer_km=None,
            notes=None,
            created_by=ids["user_id"],
            order_repo=order_repo,
            counter_repo=counter_repo,
            vehicle_repo=vehicle_repo,
        )

        for order, item_order, quantities in (
            (order_x, (ids["item_a_id"], ids["item_b_id"]), (3, 2)),
            (order_y, (ids["item_b_id"], ids["item_a_id"]), (4, 1)),
        ):
            for item_id, quantity in zip(item_order, quantities, strict=True):
                add_line(
                    workshop_id=ids["workshop_id"],
                    order_id=order.id,
                    line_id=uuid.uuid4(),
                    kind=LineKind.inventory_part,
                    item_id=item_id,
                    description="Parte",
                    quantity=quantity,
                    unit_price_cents=1000,
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
                payment_repo=SqlAlchemyPaymentRepository(setup),
            )
        setup.commit()
    try:
        yield ids
    finally:
        with Session(test_engine) as cleanup:
            cleanup.execute(
                delete(StockMovementModel).where(
                    StockMovementModel.workshop_id == ids["workshop_id"]
                )
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
            cleanup.execute(delete(ItemModel).where(ItemModel.workshop_id == ids["workshop_id"]))
            cleanup.execute(delete(VehicleModel).where(VehicleModel.id == ids["vehicle_id"]))
            cleanup.execute(delete(CustomerModel).where(CustomerModel.id == ids["customer_id"]))
            cleanup.execute(delete(UserModel).where(UserModel.id == ids["user_id"]))
            cleanup.execute(delete(WorkshopModel).where(WorkshopModel.id == ids["workshop_id"]))
            cleanup.commit()


def test_two_orders_consuming_the_same_items_in_reverse_order_do_not_deadlock(
    committed_deadlock_orders: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Defect this catches: locking inventory items in each line's own
    order (instead of `plan_reconciliation`'s deterministic sorted
    `(item_id, line_id)` order, AD-5) deadlocks two concurrent transitions
    that consume overlapping items in reverse order.
    """
    ids = committed_deadlock_orders
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def _start(order_id: uuid.UUID) -> None:
        try:
            with Session(test_engine) as session:
                barrier.wait()
                change_status(
                    workshop_id=ids["workshop_id"],
                    order_id=order_id,
                    target=WorkOrderStatus.in_progress,
                    created_by=ids["user_id"],
                    order_repo=SqlAlchemyWorkOrderRepository(session),
                    item_repo=SqlAlchemyItemRepository(session),
                    movement_repo=SqlAlchemyMovementRepository(session),
                    payment_repo=SqlAlchemyPaymentRepository(session),
                )
                session.commit()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [
        threading.Thread(target=_start, args=(ids["order_x_id"],)),
        threading.Thread(target=_start, args=(ids["order_y_id"],)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors

    with Session(test_engine) as verify:
        item_a = verify.get(ItemModel, ids["item_a_id"])
        item_b = verify.get(ItemModel, ids["item_b_id"])
        assert item_a is not None and item_b is not None
        assert item_a.stock == 10 - 3 - 1  # order_x's 3 + order_y's 1
        assert item_b.stock == 10 - 2 - 4  # order_x's 2 + order_y's 4

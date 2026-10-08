"""Concurrency tests for Factura issuance: correlative allocation
(`select_range`/`allocate`) and the order-row lock that serializes
issuance against a concurrent line edit (`design.md`'s AD-5/AD-6).

Uses two real connections and real threads, unlike the rest of the suite
(one connection per test, inside a rolled-back SAVEPOINT): an allocation
or locking race only shows up between two genuinely concurrent
transactions. Mirrors `test_work_order_concurrency.py`'s
`committed_workshop` pattern: the workshop, user, customer, vehicle and
fiscal profile this needs are committed on a separate connection, and
cleaned up on the way out -- `fiscal_invoices`/`fiscal_invoice_lines` via
`TRUNCATE` rather than `DELETE`, since AD-10's immutability trigger is
`BEFORE UPDATE OR DELETE ... FOR EACH ROW` and rejects a `DELETE`
outright; `TRUNCATE` is statement-level and never fires it.
"""

import threading
import uuid
from collections.abc import Generator
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import delete, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from taller.customers.adapters.models import CustomerModel, VehicleModel
from taller.customers.adapters.repositories import SqlAlchemyVehicleRepository
from taller.customers.domain.rtn import Rtn
from taller.identity.adapters.models import UserModel, WorkshopModel
from taller.inventory.adapters.repositories import (
    SqlAlchemyItemRepository,
    SqlAlchemyMovementRepository,
)
from taller.invoicing.adapters.models import (
    CaiRangeModel,
    FiscalInvoiceModel,
    FiscalProfileModel,
)
from taller.invoicing.adapters.repositories import (
    SqlAlchemyCaiRangeRepository,
    SqlAlchemyFiscalInvoiceRepository,
    SqlAlchemyFiscalProfileRepository,
)
from taller.invoicing.application.use_cases import issue_invoice, update_range
from taller.invoicing.domain.document_number import DocumentType
from taller.invoicing.domain.errors import CaiRangeImmutable
from taller.invoicing.domain.ranges import CaiRange
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
from taller.workorders.application.use_cases import add_line, change_status, create_work_order
from taller.workorders.domain.entities import InvoiceRef, LineKind
from taller.workorders.domain.errors import WorkOrderInvoiced
from taller.workorders.domain.status import WorkOrderStatus

#: Fixed phone for this fixture's committed user row (must be unique, 8
#: digits, and unused by any other test's committed data).
_PHONE = "87650088"


class _RealClock:
    """`issue_invoice`'s `Clock` dependency, using the real wall clock --
    every range deadline in this file is set far enough out that the
    exact moment does not matter.
    """

    def now(self) -> datetime:
        return datetime.now(UTC)


class _PausingOrderRepository:
    """Wraps the real repository so a test can force a specific arrival
    order at the order-row lock: `get_for_update` signals `acquired` once
    the real Postgres lock is held, then blocks on `release` before
    returning -- giving the other side's own `get_for_update` call time
    to actually reach Postgres and block on that same real row lock.
    Mirrors `test_work_order_concurrency.py`'s
    `_ReadPausingWorkOrderRepository`.
    """

    def __init__(
        self,
        inner: SqlAlchemyWorkOrderRepository,
        acquired: threading.Event,
        release: threading.Event,
    ) -> None:
        self._inner = inner
        self._acquired = acquired
        self._release = release

    def get_for_update(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID):
        order = self._inner.get_for_update(workshop_id=workshop_id, order_id=order_id)
        self._acquired.set()
        self._release.wait(timeout=5)
        return order

    def active_invoice(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> InvoiceRef | None:
        return self._inner.active_invoice(workshop_id=workshop_id, order_id=order_id)

    def save(self, order) -> None:
        self._inner.save(order)


class _PausingCaiRangeRepository:
    """Wraps the real repository so a test can force a concurrent
    allocation to land in the window `update_range()` leaves open between
    its first, unlocked `get_by_id()` read and the fiscal-profile lock it
    only then acquires: `get_by_id` signals `acquired` once it has
    returned that first, soon-to-be-stale snapshot, then blocks on
    `release` before letting the caller continue towards the lock. Only
    the first call pauses; a second call (a fixed `update_range()`
    re-reading the range under the lock) returns immediately. Mirrors
    `_PausingOrderRepository` above.
    """

    def __init__(
        self,
        inner: SqlAlchemyCaiRangeRepository,
        acquired: threading.Event,
        release: threading.Event,
    ) -> None:
        self._inner = inner
        self._acquired = acquired
        self._release = release
        self._calls = 0

    def get_by_id(self, *, workshop_id: uuid.UUID, range_id: uuid.UUID):
        result = self._inner.get_by_id(workshop_id=workshop_id, range_id=range_id)
        self._calls += 1
        if self._calls == 1:
            self._acquired.set()
            self._release.wait(timeout=5)
        return result

    def list(self, *, workshop_id: uuid.UUID, document_type: DocumentType | None = None):
        return self._inner.list(workshop_id=workshop_id, document_type=document_type)

    def add(self, cai_range: CaiRange) -> None:
        self._inner.add(cai_range)

    def save(self, cai_range: CaiRange) -> None:
        self._inner.save(cai_range)

    def allocate(self, *, range_id: uuid.UUID, now: datetime) -> int | None:
        return self._inner.allocate(range_id=range_id, now=now)


@pytest.fixture
def committed_invoicing_workshop(test_engine: Engine) -> Generator[dict[str, uuid.UUID]]:
    """A real workshop, owner user, customer, vehicle and a complete
    fiscal profile, committed on a connection separate from the per-test
    SAVEPOINT, so independent `Session(test_engine)` connections can
    genuinely race against the same profile/range rows the way two
    concurrent HTTP requests would.
    """
    ids = {
        "workshop_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "customer_id": uuid.uuid4(),
        "vehicle_id": uuid.uuid4(),
    }
    now = datetime.now(UTC)
    with Session(test_engine) as setup:
        setup.add(
            WorkshopModel(id=ids["workshop_id"], name="Taller Concurrencia Fiscal", created_at=now)
        )
        setup.flush()
        setup.add(
            UserModel(
                id=ids["user_id"],
                workshop_id=ids["workshop_id"],
                full_name="Owner Fiscal",
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
                full_name="Cliente Fiscal",
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
        setup.add(
            FiscalProfileModel(
                workshop_id=ids["workshop_id"],
                rtn=Rtn.from_raw("0801-1990-123456"),
                legal_name="Taller Don Chepe S. de R.L.",
                trade_name="Taller Don Chepe",
                address="Barrio El Centro, Tegucigalpa",
                phone="22001100",
                email="contacto@tallerdonchepe.example",
                establishment_code="001",
                emission_point_code="001",
                created_at=now,
                updated_at=now,
            )
        )
        setup.commit()
    try:
        yield ids
    finally:
        with Session(test_engine) as cleanup:
            cleanup.execute(text("TRUNCATE TABLE fiscal_invoice_lines, fiscal_invoices"))
            cleanup.execute(
                delete(CaiRangeModel).where(CaiRangeModel.workshop_id == ids["workshop_id"])
            )
            cleanup.execute(
                delete(FiscalProfileModel).where(
                    FiscalProfileModel.workshop_id == ids["workshop_id"]
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
            cleanup.execute(delete(VehicleModel).where(VehicleModel.id == ids["vehicle_id"]))
            cleanup.execute(delete(CustomerModel).where(CustomerModel.id == ids["customer_id"]))
            cleanup.execute(delete(UserModel).where(UserModel.id == ids["user_id"]))
            cleanup.execute(delete(WorkshopModel).where(WorkshopModel.id == ids["workshop_id"]))
            cleanup.commit()


def _add_range(
    session: Session,
    *,
    workshop_id: uuid.UUID,
    created_by: uuid.UUID,
    range_start: int,
    range_end: int,
    issue_deadline: date,
) -> uuid.UUID:
    range_id = uuid.uuid4()
    now = datetime.now(UTC)
    SqlAlchemyCaiRangeRepository(session).add(
        CaiRange(
            id=range_id,
            workshop_id=workshop_id,
            document_type=DocumentType.invoice,
            cai="A1B2C3D4E5",
            establishment_code="001",
            emission_point_code="001",
            range_start=range_start,
            range_end=range_end,
            next_number=range_start,
            issue_deadline=issue_deadline,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
    )
    session.commit()
    return range_id


def _create_completed_order(session: Session, ids: dict[str, uuid.UUID]) -> uuid.UUID:
    """A work order with one labor line, walked to `completed` -- eligible
    for issuance.
    """
    order_id = uuid.uuid4()
    order_repo = SqlAlchemyWorkOrderRepository(session)
    item_repo = SqlAlchemyItemRepository(session)
    movement_repo = SqlAlchemyMovementRepository(session)
    payment_repo = SqlAlchemyPaymentRepository(session)
    create_work_order(
        workshop_id=ids["workshop_id"],
        order_id=order_id,
        vehicle_id=ids["vehicle_id"],
        complaint=None,
        odometer_km=None,
        notes=None,
        created_by=ids["user_id"],
        order_repo=order_repo,
        counter_repo=SqlAlchemyWorkshopCounterRepository(session),
        vehicle_repo=SqlAlchemyVehicleRepository(session),
    )
    add_line(
        workshop_id=ids["workshop_id"],
        order_id=order_id,
        line_id=uuid.uuid4(),
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
    for target in (
        WorkOrderStatus.approved,
        WorkOrderStatus.in_progress,
        WorkOrderStatus.completed,
    ):
        change_status(
            workshop_id=ids["workshop_id"],
            order_id=order_id,
            target=target,
            created_by=ids["user_id"],
            order_repo=order_repo,
            item_repo=item_repo,
            movement_repo=movement_repo,
            payment_repo=payment_repo,
        )
    session.commit()
    return order_id


def _issue(session: Session, *, workshop_id: uuid.UUID, order_id: uuid.UUID, created_by: uuid.UUID):
    return issue_invoice(
        workshop_id=workshop_id,
        invoice_id=uuid.uuid4(),
        order_id=order_id,
        buyer_name=None,
        buyer_rtn=None,
        created_by=created_by,
        clock=_RealClock(),
        order_repo=SqlAlchemyWorkOrderRepository(session),
        profile_repo=SqlAlchemyFiscalProfileRepository(session),
        range_repo=SqlAlchemyCaiRangeRepository(session),
        invoice_repo=SqlAlchemyFiscalInvoiceRepository(session),
    )


def test_allocate_eight_concurrent_racers_against_a_fresh_range_never_duplicates_or_skips(
    committed_invoicing_workshop: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Drives `SqlAlchemyCaiRangeRepository.allocate` directly at the
    repository seam -- no fiscal-profile lock in play -- covering
    `cai-ranges/spec.md`'s "Correlative Allocation Is Gap-Free And
    Row-Locked Under Concurrency" scenario ("concurrent issuance never
    skips or duplicates a number").

    Defect this catches: replacing `allocate`'s atomic `UPDATE ...
    RETURNING` with a read-then-write (`SELECT next_number`, then
    `UPDATE ... SET next_number = :read + 1`, no row lock) loses updates
    under concurrency, handing the same correlative to more than one
    racer or skipping one entirely.
    """
    ids = committed_invoicing_workshop
    racer_count = 8
    with Session(test_engine) as setup:
        range_id = _add_range(
            setup,
            workshop_id=ids["workshop_id"],
            created_by=ids["user_id"],
            range_start=1,
            range_end=racer_count,
            issue_deadline=date.today() + timedelta(days=300),
        )

    barrier = threading.Barrier(racer_count)
    results: list[int | None] = []
    errors: list[BaseException] = []

    def _allocate_once() -> None:
        try:
            with Session(test_engine) as session:
                barrier.wait()
                correlative = SqlAlchemyCaiRangeRepository(session).allocate(
                    range_id=range_id, now=datetime.now(UTC)
                )
                session.commit()
                results.append(correlative)
        except BaseException as exc:  # noqa: BLE001 -- surfaced via `errors` below
            errors.append(exc)

    threads = [threading.Thread(target=_allocate_once) for _ in range(racer_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert sorted(results) == list(range(1, racer_count + 1))


def test_concurrent_issuances_with_the_same_invoice_id_allocate_exactly_once(
    committed_invoicing_workshop: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Defect this catches: a rolled-back duplicate insert on a retried
    issuance leaves a gap in the correlative sequence, or allocates the
    same number twice.
    """
    ids = committed_invoicing_workshop
    with Session(test_engine) as setup:
        order_id = _create_completed_order(setup, ids)
        _add_range(
            setup,
            workshop_id=ids["workshop_id"],
            created_by=ids["user_id"],
            range_start=1,
            range_end=100,
            issue_deadline=date.today() + timedelta(days=300),
        )
    invoice_id = uuid.uuid4()
    barrier = threading.Barrier(2)
    outcomes: list[bool] = []
    errors: list[BaseException] = []

    def _issue_once(session: Session) -> tuple[object, bool]:
        return issue_invoice(
            workshop_id=ids["workshop_id"],
            invoice_id=invoice_id,
            order_id=order_id,
            buyer_name=None,
            buyer_rtn=None,
            created_by=ids["user_id"],
            clock=_RealClock(),
            order_repo=SqlAlchemyWorkOrderRepository(session),
            profile_repo=SqlAlchemyFiscalProfileRepository(session),
            range_repo=SqlAlchemyCaiRangeRepository(session),
            invoice_repo=SqlAlchemyFiscalInvoiceRepository(session),
        )

    def _issue_with_retry() -> None:
        try:
            with Session(test_engine) as session:
                barrier.wait()
                try:
                    _, is_new = _issue_once(session)
                    session.commit()
                except IntegrityError:
                    # Mirrors the router's own retry-once-on-IntegrityError
                    # dance (`issue_invoice_route`): the rollback below
                    # undoes this attempt's allocated correlative, so the
                    # retry's replay-check finds the row the other thread
                    # just committed and never burns a second number.
                    session.rollback()
                    _, is_new = _issue_once(session)
                    session.commit()
                outcomes.append(is_new)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_issue_with_retry) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert sorted(outcomes) == [False, True]

    with Session(test_engine) as verify:
        rows = (
            verify.query(FiscalInvoiceModel)
            .filter(
                FiscalInvoiceModel.workshop_id == ids["workshop_id"],
                FiscalInvoiceModel.id == invoice_id,
            )
            .all()
        )
        assert len(rows) == 1

        range_row = (
            verify.query(CaiRangeModel)
            .filter(CaiRangeModel.workshop_id == ids["workshop_id"])
            .one()
        )
        assert range_row.next_number == 2


def test_allocate_gives_the_last_number_to_exactly_one_of_two_racers(
    committed_invoicing_workshop: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Drives `SqlAlchemyCaiRangeRepository.allocate` directly at the
    repository seam -- no fiscal-profile lock in play -- covering
    `cai-ranges/spec.md`'s "Issuance Is Blocked When The Active Range Is
    Exhausted" scenario ("the last number in a range is allocated
    normally" / "issuance is blocked once the range is exhausted").

    Defect this catches: dropping `allocate`'s `next_number <= range_end`
    `WHERE` condition lets the second racer allocate a number past
    `range_end` instead of getting `None`.
    """
    ids = committed_invoicing_workshop
    with Session(test_engine) as setup:
        range_id = _add_range(
            setup,
            workshop_id=ids["workshop_id"],
            created_by=ids["user_id"],
            range_start=1,
            range_end=1,
            issue_deadline=date.today() + timedelta(days=300),
        )

    results: list[int | None] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(2)

    def _allocate_once() -> None:
        try:
            with Session(test_engine) as session:
                barrier.wait()
                correlative = SqlAlchemyCaiRangeRepository(session).allocate(
                    range_id=range_id, now=datetime.now(UTC)
                )
                session.commit()
                results.append(correlative)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_allocate_once) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert results.count(1) == 1
    assert results.count(None) == 1

    with Session(test_engine) as verify:
        range_row = verify.query(CaiRangeModel).filter(CaiRangeModel.id == range_id).one()
        # The winning racer's allocation (range_start -> range_end + 1)
        # must never be exceeded by the loser.
        assert range_row.next_number == 2


def test_a_standby_range_takes_over_when_the_active_one_runs_out_mid_burst(
    committed_invoicing_workshop: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Defect this catches: range selection racing against allocation so
    the second issuer sees the just-emptied range as still active and
    gets a false `cai_range_exhausted` instead of falling through to the
    standby range with a later fecha límite.
    """
    ids = committed_invoicing_workshop
    with Session(test_engine) as setup:
        order_ids = [_create_completed_order(setup, ids) for _ in range(2)]
        _add_range(
            setup,
            workshop_id=ids["workshop_id"],
            created_by=ids["user_id"],
            range_start=1,
            range_end=1,
            issue_deadline=date.today() + timedelta(days=10),
        )
        _add_range(
            setup,
            workshop_id=ids["workshop_id"],
            created_by=ids["user_id"],
            range_start=2,
            range_end=101,
            issue_deadline=date.today() + timedelta(days=300),
        )

    correlatives: list[int] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(2)

    def _run(order_id: uuid.UUID) -> None:
        try:
            with Session(test_engine) as session:
                barrier.wait()
                invoice, _ = _issue(
                    session,
                    workshop_id=ids["workshop_id"],
                    order_id=order_id,
                    created_by=ids["user_id"],
                )
                session.commit()
                correlatives.append(invoice.correlative)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_run, args=(order_id,)) for order_id in order_ids]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert sorted(correlatives) == [1, 2]


def test_add_line_committed_first_is_reflected_in_a_concurrent_issuance_snapshot(
    committed_invoicing_workshop: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Defect this catches: the invoice snapshot and a concurrent line
    edit are not serialized on the order-row lock, so a Factura could be
    issued without a line that actually committed just before it did.
    """
    ids = committed_invoicing_workshop
    with Session(test_engine) as setup:
        order_id = _create_completed_order(setup, ids)
        _add_range(
            setup,
            workshop_id=ids["workshop_id"],
            created_by=ids["user_id"],
            range_start=1,
            range_end=10,
            issue_deadline=date.today() + timedelta(days=300),
        )

    acquired = threading.Event()
    release = threading.Event()
    errors: list[BaseException] = []
    results: dict[str, object] = {}

    def _edit() -> None:
        try:
            with Session(test_engine) as session:
                order_repo = _PausingOrderRepository(
                    SqlAlchemyWorkOrderRepository(session), acquired, release
                )
                add_line(
                    workshop_id=ids["workshop_id"],
                    order_id=order_id,
                    line_id=uuid.uuid4(),
                    kind=LineKind.labor,
                    item_id=None,
                    description="Alineado y balanceo",
                    quantity=1,
                    unit_price_cents=30000,
                    created_by=ids["user_id"],
                    order_repo=order_repo,
                    item_repo=SqlAlchemyItemRepository(session),
                    movement_repo=SqlAlchemyMovementRepository(session),
                )
                session.commit()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    def _issue_after_acquired() -> None:
        acquired.wait(timeout=5)
        try:
            with Session(test_engine) as session:
                invoice, _ = _issue(
                    session,
                    workshop_id=ids["workshop_id"],
                    order_id=order_id,
                    created_by=ids["user_id"],
                )
                session.commit()
                results["invoice"] = invoice
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    editor = threading.Thread(target=_edit)
    issuer = threading.Thread(target=_issue_after_acquired)
    editor.start()
    issuer.start()
    acquired.wait(timeout=5)
    release.set()
    editor.join()
    issuer.join()

    assert not errors, errors
    invoice = results["invoice"]
    assert len(invoice.lines) == 2


def test_issuance_committed_first_locks_out_a_concurrent_line_edit(
    committed_invoicing_workshop: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Defect this catches: the invoice snapshot and a concurrent line
    edit are not serialized on the order-row lock, so a line could be
    added to an order right after its Factura was issued without ever
    hitting `work_order_invoiced`.
    """
    ids = committed_invoicing_workshop
    with Session(test_engine) as setup:
        order_id = _create_completed_order(setup, ids)
        _add_range(
            setup,
            workshop_id=ids["workshop_id"],
            created_by=ids["user_id"],
            range_start=1,
            range_end=10,
            issue_deadline=date.today() + timedelta(days=300),
        )

    acquired = threading.Event()
    release = threading.Event()
    errors: list[BaseException] = []
    results: dict[str, object] = {}

    def _issue_first() -> None:
        try:
            with Session(test_engine) as session:
                order_repo = _PausingOrderRepository(
                    SqlAlchemyWorkOrderRepository(session), acquired, release
                )
                invoice, _ = issue_invoice(
                    workshop_id=ids["workshop_id"],
                    invoice_id=uuid.uuid4(),
                    order_id=order_id,
                    buyer_name=None,
                    buyer_rtn=None,
                    created_by=ids["user_id"],
                    clock=_RealClock(),
                    order_repo=order_repo,
                    profile_repo=SqlAlchemyFiscalProfileRepository(session),
                    range_repo=SqlAlchemyCaiRangeRepository(session),
                    invoice_repo=SqlAlchemyFiscalInvoiceRepository(session),
                )
                session.commit()
                results["invoice"] = invoice
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    def _edit_after_acquired() -> None:
        acquired.wait(timeout=5)
        try:
            with Session(test_engine) as session:
                add_line(
                    workshop_id=ids["workshop_id"],
                    order_id=order_id,
                    line_id=uuid.uuid4(),
                    kind=LineKind.labor,
                    item_id=None,
                    description="Alineado y balanceo",
                    quantity=1,
                    unit_price_cents=30000,
                    created_by=ids["user_id"],
                    order_repo=SqlAlchemyWorkOrderRepository(session),
                    item_repo=SqlAlchemyItemRepository(session),
                    movement_repo=SqlAlchemyMovementRepository(session),
                )
                session.commit()
        except WorkOrderInvoiced as exc:
            results["edit_error"] = exc
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    issuer = threading.Thread(target=_issue_first)
    editor = threading.Thread(target=_edit_after_acquired)
    issuer.start()
    editor.start()
    acquired.wait(timeout=5)
    release.set()
    issuer.join()
    editor.join()

    assert not errors, errors
    assert "invoice" in results
    assert isinstance(results.get("edit_error"), WorkOrderInvoiced)


def test_update_range_does_not_un_consume_a_number_allocated_during_its_unlocked_read(
    committed_invoicing_workshop: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Defect this catches: `update_range()` reads the CAI range before
    taking the fiscal-profile lock (AD-5), so a concurrent
    `issue_invoice()` that allocates and commits a correlative in that
    window is invisible to the immutability check that follows the lock
    -- letting the PATCH report success and reset `next_number` back to
    `range_start`, silently un-consuming a correlative an immutable,
    already-committed Factura still references.
    """
    ids = committed_invoicing_workshop
    with Session(test_engine) as setup:
        order_id = _create_completed_order(setup, ids)
        range_id = _add_range(
            setup,
            workshop_id=ids["workshop_id"],
            created_by=ids["user_id"],
            range_start=1,
            range_end=100,
            issue_deadline=date.today() + timedelta(days=300),
        )

    acquired = threading.Event()
    release = threading.Event()
    errors: list[BaseException] = []

    def _patch_range() -> None:
        try:
            with Session(test_engine) as session:
                range_repo = _PausingCaiRangeRepository(
                    SqlAlchemyCaiRangeRepository(session), acquired, release
                )
                update_range(
                    workshop_id=ids["workshop_id"],
                    range_id=range_id,
                    fields={"issue_deadline": date.today() + timedelta(days=301)},
                    clock=_RealClock(),
                    profile_repo=SqlAlchemyFiscalProfileRepository(session),
                    range_repo=range_repo,
                )
                session.commit()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            acquired.set()

    patcher = threading.Thread(target=_patch_range)
    patcher.start()
    assert acquired.wait(timeout=5)

    with Session(test_engine) as session:
        _issue(
            session,
            workshop_id=ids["workshop_id"],
            order_id=order_id,
            created_by=ids["user_id"],
        )
        session.commit()

    release.set()
    patcher.join(timeout=5)

    assert len(errors) == 1, errors
    assert isinstance(errors[0], CaiRangeImmutable)

    with Session(test_engine) as verify:
        range_row = verify.query(CaiRangeModel).filter(CaiRangeModel.id == range_id).one()
        # The issuance's allocation (range_start -> range_start + 1) must
        # survive the PATCH, not be reset back to range_start.
        assert range_row.next_number == 2

"""Concurrency test for credit-note issuance: the order-row and
invoice-row locks (`design.md`'s AD-5/AD-13) that must serialize two
credit notes racing against the same Factura.

Uses two real connections and real threads, like
`test_invoice_concurrency.py`: a locking race only shows up between two
genuinely concurrent transactions. The committed workshop/user/customer/
vehicle/fiscal-profile fixture below mirrors that file's
`committed_invoicing_workshop` (duplicated locally rather than imported,
matching this suite's one-file-per-concurrency-scenario convention).
"""

import threading
import uuid
from collections.abc import Generator
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import delete, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from taller.customers.adapters.models import CustomerModel, VehicleModel
from taller.customers.adapters.repositories import SqlAlchemyVehicleRepository
from taller.customers.domain.rtn import Rtn
from taller.identity.adapters.models import UserModel, WorkshopModel
from taller.inventory.adapters.repositories import (
    SqlAlchemyItemRepository,
    SqlAlchemyMovementRepository,
)
from taller.invoicing.adapters.models import CaiRangeModel, FiscalProfileModel
from taller.invoicing.adapters.repositories import (
    SqlAlchemyCaiRangeRepository,
    SqlAlchemyCreditNoteRepository,
    SqlAlchemyFiscalInvoiceRepository,
    SqlAlchemyFiscalProfileRepository,
)
from taller.invoicing.application.use_cases import issue_credit_note, issue_invoice
from taller.invoicing.domain.document_number import DocumentType
from taller.invoicing.domain.errors import InvoiceAlreadyCredited
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
from taller.workorders.domain.entities import LineKind
from taller.workorders.domain.status import WorkOrderStatus

#: Fixed phone for this fixture's committed user row (must be unique, 8
#: digits, and unused by any other test's committed data).
_PHONE = "87650188"


class _RealClock:
    """`issue_invoice`/`issue_credit_note`'s `Clock` dependency, using the
    real wall clock -- every range deadline in this file is set far
    enough out that the exact moment does not matter.
    """

    def now(self) -> datetime:
        return datetime.now(UTC)


@pytest.fixture
def committed_credit_note_workshop(test_engine: Engine) -> Generator[dict[str, uuid.UUID]]:
    """A real workshop, owner user, customer, vehicle and a complete
    fiscal profile, committed on a connection separate from the per-test
    SAVEPOINT, so independent `Session(test_engine)` connections can
    genuinely race against the same invoice/range rows the way two
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
            WorkshopModel(id=ids["workshop_id"], name="Taller Concurrencia Credito", created_at=now)
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
            # `fiscal_credit_notes` FK-references `fiscal_invoices`, so
            # Postgres requires both in the same TRUNCATE statement.
            cleanup.execute(
                text("TRUNCATE TABLE fiscal_credit_notes, fiscal_invoice_lines, fiscal_invoices")
            )
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
    document_type: DocumentType,
    cai: str,
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
            document_type=document_type,
            cai=cai,
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


def test_two_concurrent_credit_notes_against_one_factura_credit_it_exactly_once(
    committed_credit_note_workshop: dict[str, uuid.UUID], test_engine: Engine
) -> None:
    """Defect this catches: a credit race without the order-row and
    invoice-row locks lets both succeed, double-crediting one Factura
    and consuming two `06` correlatives instead of one.
    """
    ids = committed_credit_note_workshop
    with Session(test_engine) as setup:
        order_id = _create_completed_order(setup, ids)
        _add_range(
            setup,
            workshop_id=ids["workshop_id"],
            created_by=ids["user_id"],
            document_type=DocumentType.invoice,
            cai="A1B2C3D4E5",
            range_start=1,
            range_end=10,
            issue_deadline=date.today() + timedelta(days=300),
        )
        credit_range_id = _add_range(
            setup,
            workshop_id=ids["workshop_id"],
            created_by=ids["user_id"],
            document_type=DocumentType.credit_note,
            cai="B2C3D4E5F6",
            range_start=1,
            range_end=10,
            issue_deadline=date.today() + timedelta(days=300),
        )
        invoice, _ = issue_invoice(
            workshop_id=ids["workshop_id"],
            invoice_id=uuid.uuid4(),
            order_id=order_id,
            buyer_name=None,
            buyer_rtn=None,
            created_by=ids["user_id"],
            clock=_RealClock(),
            order_repo=SqlAlchemyWorkOrderRepository(setup),
            profile_repo=SqlAlchemyFiscalProfileRepository(setup),
            range_repo=SqlAlchemyCaiRangeRepository(setup),
            invoice_repo=SqlAlchemyFiscalInvoiceRepository(setup),
        )
        setup.commit()
        invoice_id = invoice.id

    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    errors: list[BaseException] = []

    def _credit_once() -> None:
        try:
            with Session(test_engine) as session:
                barrier.wait()
                try:
                    issue_credit_note(
                        workshop_id=ids["workshop_id"],
                        credit_note_id=uuid.uuid4(),
                        invoice_id=invoice_id,
                        reason="Servicio cancelado por el cliente",
                        created_by=ids["user_id"],
                        clock=_RealClock(),
                        order_repo=SqlAlchemyWorkOrderRepository(session),
                        profile_repo=SqlAlchemyFiscalProfileRepository(session),
                        range_repo=SqlAlchemyCaiRangeRepository(session),
                        invoice_repo=SqlAlchemyFiscalInvoiceRepository(session),
                        credit_note_repo=SqlAlchemyCreditNoteRepository(session),
                    )
                    session.commit()
                    outcomes.append("success")
                except InvoiceAlreadyCredited:
                    session.rollback()
                    outcomes.append("already_credited")
        except BaseException as exc:  # noqa: BLE001 -- surfaced via `errors` below
            errors.append(exc)

    threads = [threading.Thread(target=_credit_once) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert sorted(outcomes) == ["already_credited", "success"]

    with Session(test_engine) as verify:
        range_row = verify.query(CaiRangeModel).filter(CaiRangeModel.id == credit_range_id).one()
        # Only the winning racer's allocation must be consumed: the loser
        # raised before ever calling `range_repo.allocate`.
        assert range_row.next_number == 2

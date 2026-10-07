"""SQLAlchemy adapters for the work-orders feature's repositories."""

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import BigInteger, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from taller.workorders.adapters.models import (
    PaymentModel,
    WorkOrderLineModel,
    WorkOrderModel,
    WorkshopCounterModel,
)
from taller.workorders.domain.entities import (
    LineKind,
    Payment,
    PaymentMethod,
    WorkOrder,
    WorkOrderLine,
)
from taller.workorders.domain.status import WorkOrderStatus


class SqlAlchemyWorkshopCounterRepository:
    """Per-workshop named counter persistence backed by SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def next_value(self, *, workshop_id: uuid.UUID, name: str) -> int:
        """`design.md`'s AD-6 upsert: no counter row has to exist
        beforehand, and the statement itself holds the row lock until the
        caller's transaction commits or rolls back.
        """
        statement = (
            pg_insert(WorkshopCounterModel)
            .values(workshop_id=workshop_id, name=name, value=1)
            .on_conflict_do_update(
                index_elements=[WorkshopCounterModel.workshop_id, WorkshopCounterModel.name],
                set_={"value": WorkshopCounterModel.value + 1},
            )
            .returning(WorkshopCounterModel.value)
        )
        return self._session.execute(statement).scalar_one()


def _line_from_model(model: WorkOrderLineModel) -> WorkOrderLine:
    return WorkOrderLine(
        id=model.id,
        workshop_id=model.workshop_id,
        order_id=model.order_id,
        kind=LineKind(model.kind),
        item_id=model.item_id,
        description=model.description,
        quantity=model.quantity,
        unit_price_cents=model.unit_price_cents,
        stock_posted_quantity=model.stock_posted_quantity,
        stock_revision=model.stock_revision,
        removed_at=model.removed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _order_from_model(model: WorkOrderModel, lines: list[WorkOrderLine]) -> WorkOrder:
    return WorkOrder(
        id=model.id,
        workshop_id=model.workshop_id,
        number=model.number,
        vehicle_id=model.vehicle_id,
        customer_id=model.customer_id,
        status=WorkOrderStatus(model.status),
        complaint=model.complaint,
        odometer_km=model.odometer_km,
        notes=model.notes,
        created_by=model.created_by,
        approved_at=model.approved_at,
        started_at=model.started_at,
        completed_at=model.completed_at,
        delivered_at=model.delivered_at,
        cancelled_at=model.cancelled_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
        lines=lines,
    )


class SqlAlchemyWorkOrderRepository:
    """Work order (and its lines) persistence backed by SQLAlchemy.

    ``work_order_lines`` has no ORM ``relationship()`` to ``work_orders``
    (every model in this codebase maps 1:1 to its own table, with
    cross-table links as explicit queries -- see P2.S1's note that
    SQLAlchemy's flush does not auto-order inserts across unrelated
    mapped classes), so ``get_by_id``/``get_for_update``/``save`` all
    load and persist the lines collection explicitly, instead of through
    a mapped collection.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> WorkOrder | None:
        model = (
            self._session.query(WorkOrderModel)
            .filter(WorkOrderModel.id == order_id, WorkOrderModel.workshop_id == workshop_id)
            .one_or_none()
        )
        if model is None:
            return None
        return _order_from_model(model, self._lines_for(order_id))

    def get_for_update(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> WorkOrder | None:
        model = (
            self._session.query(WorkOrderModel)
            .filter(WorkOrderModel.id == order_id, WorkOrderModel.workshop_id == workshop_id)
            .with_for_update()
            .one_or_none()
        )
        if model is None:
            return None
        return _order_from_model(model, self._lines_for(order_id))

    def _lines_for(self, order_id: uuid.UUID) -> list[WorkOrderLine]:
        rows = (
            self._session.query(WorkOrderLineModel)
            .filter(WorkOrderLineModel.order_id == order_id)
            .order_by(WorkOrderLineModel.created_at, WorkOrderLineModel.id)
            .all()
        )
        return [_line_from_model(row) for row in rows]

    def _add_line_model(self, line: WorkOrderLine) -> None:
        self._session.add(
            WorkOrderLineModel(
                id=line.id,
                workshop_id=line.workshop_id,
                order_id=line.order_id,
                kind=line.kind.value,
                item_id=line.item_id,
                description=line.description,
                quantity=line.quantity,
                unit_price_cents=line.unit_price_cents,
                stock_posted_quantity=line.stock_posted_quantity,
                stock_revision=line.stock_revision,
                removed_at=line.removed_at,
                created_at=line.created_at,
                updated_at=line.updated_at,
            )
        )

    def add(self, order: WorkOrder) -> None:
        self._session.add(
            WorkOrderModel(
                id=order.id,
                workshop_id=order.workshop_id,
                number=order.number,
                vehicle_id=order.vehicle_id,
                customer_id=order.customer_id,
                status=order.status.value,
                complaint=order.complaint,
                odometer_km=order.odometer_km,
                notes=order.notes,
                created_by=order.created_by,
                approved_at=order.approved_at,
                started_at=order.started_at,
                completed_at=order.completed_at,
                delivered_at=order.delivered_at,
                cancelled_at=order.cancelled_at,
                created_at=order.created_at,
                updated_at=order.updated_at,
            )
        )
        self._session.flush()
        for line in order.lines:
            self._add_line_model(line)
        if order.lines:
            self._session.flush()

    def save(self, order: WorkOrder) -> None:
        model = self._session.get(WorkOrderModel, order.id)
        if model is None:
            return
        model.status = order.status.value
        model.complaint = order.complaint
        model.odometer_km = order.odometer_km
        model.notes = order.notes
        model.approved_at = order.approved_at
        model.started_at = order.started_at
        model.completed_at = order.completed_at
        model.delivered_at = order.delivered_at
        model.cancelled_at = order.cancelled_at
        model.updated_at = order.updated_at

        existing_rows = {
            row.id: row
            for row in self._session.query(WorkOrderLineModel).filter(
                WorkOrderLineModel.order_id == order.id
            )
        }
        for line in order.lines:
            line_model = existing_rows.get(line.id)
            if line_model is not None:
                line_model.description = line.description
                line_model.quantity = line.quantity
                line_model.unit_price_cents = line.unit_price_cents
                line_model.stock_posted_quantity = line.stock_posted_quantity
                line_model.stock_revision = line.stock_revision
                line_model.removed_at = line.removed_at
                line_model.updated_at = line.updated_at
            else:
                self._add_line_model(line)
        self._session.flush()

    def list(
        self,
        *,
        workshop_id: uuid.UUID,
        statuses: frozenset[WorkOrderStatus] | None,
        vehicle_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
        before_number: int | None,
        limit: int,
    ) -> list[WorkOrder]:
        q = self._session.query(WorkOrderModel).filter(WorkOrderModel.workshop_id == workshop_id)
        if statuses is not None:
            q = q.filter(WorkOrderModel.status.in_([status.value for status in statuses]))
        if vehicle_id is not None:
            q = q.filter(WorkOrderModel.vehicle_id == vehicle_id)
        if customer_id is not None:
            q = q.filter(WorkOrderModel.customer_id == customer_id)
        if before_number is not None:
            q = q.filter(WorkOrderModel.number < before_number)
        q = q.order_by(WorkOrderModel.number.desc()).limit(limit)
        return [_order_from_model(model, []) for model in q.all()]

    def totals(
        self, *, workshop_id: uuid.UUID, order_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        if not order_ids:
            return {}
        # Cast to bigint before multiplying: an int4 * int4 product can
        # overflow before SUM widens it (design.md's AD-10).
        subtotal = (
            WorkOrderLineModel.quantity.cast(BigInteger) * WorkOrderLineModel.unit_price_cents
        )
        rows = (
            self._session.query(WorkOrderLineModel.order_id, func.sum(subtotal))
            .filter(
                WorkOrderLineModel.workshop_id == workshop_id,
                WorkOrderLineModel.order_id.in_(order_ids),
                WorkOrderLineModel.removed_at.is_(None),
            )
            .group_by(WorkOrderLineModel.order_id)
            .all()
        )
        totals = {order_id: int(total) for order_id, total in rows}
        return {order_id: totals.get(order_id, 0) for order_id in order_ids}

    def numbers(
        self, *, workshop_id: uuid.UUID, order_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        if not order_ids:
            return {}
        rows = (
            self._session.query(WorkOrderModel.id, WorkOrderModel.number)
            .filter(
                WorkOrderModel.workshop_id == workshop_id,
                WorkOrderModel.id.in_(order_ids),
            )
            .all()
        )
        return {order_id: number for order_id, number in rows}


def _payment_from_model(model: PaymentModel) -> Payment:
    return Payment(
        id=model.id,
        workshop_id=model.workshop_id,
        order_id=model.order_id,
        amount_cents=model.amount_cents,
        method=PaymentMethod(model.method),
        note=model.note,
        paid_at=model.paid_at,
        voided_at=model.voided_at,
        void_reason=model.void_reason,
        created_by=model.created_by,
        created_at=model.created_at,
    )


class SqlAlchemyPaymentRepository:
    """Payment persistence backed by SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(
        self, *, workshop_id: uuid.UUID, order_id: uuid.UUID, payment_id: uuid.UUID
    ) -> Payment | None:
        model = (
            self._session.query(PaymentModel)
            .filter(
                PaymentModel.id == payment_id,
                PaymentModel.order_id == order_id,
                PaymentModel.workshop_id == workshop_id,
            )
            .one_or_none()
        )
        if model is None:
            return None
        return _payment_from_model(model)

    def add(self, payment: Payment) -> None:
        self._session.add(
            PaymentModel(
                id=payment.id,
                workshop_id=payment.workshop_id,
                order_id=payment.order_id,
                amount_cents=payment.amount_cents,
                method=payment.method.value,
                note=payment.note,
                paid_at=payment.paid_at,
                voided_at=payment.voided_at,
                void_reason=payment.void_reason,
                created_by=payment.created_by,
                created_at=payment.created_at,
            )
        )
        self._session.flush()

    def save(self, payment: Payment) -> None:
        model = self._session.get(PaymentModel, payment.id)
        if model is None:
            return
        model.voided_at = payment.voided_at
        model.void_reason = payment.void_reason
        self._session.flush()

    def list_for_order(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> list[Payment]:
        rows = (
            self._session.query(PaymentModel)
            .filter(PaymentModel.workshop_id == workshop_id, PaymentModel.order_id == order_id)
            .order_by(PaymentModel.paid_at, PaymentModel.id)
            .all()
        )
        return [_payment_from_model(row) for row in rows]

    def list_for_workshop_day(
        self, *, workshop_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[Payment]:
        rows = (
            self._session.query(PaymentModel)
            .filter(
                PaymentModel.workshop_id == workshop_id,
                PaymentModel.paid_at >= start,
                PaymentModel.paid_at < end,
            )
            .order_by(PaymentModel.paid_at, PaymentModel.id)
            .all()
        )
        return [_payment_from_model(row) for row in rows]

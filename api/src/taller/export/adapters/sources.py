"""Workshop-scoped read-only sources for the data export.

Each function below queries an explicit column list directly against one
feature's ORM models -- never through that feature's repository or domain
layer -- always filtered by `workshop_id` (`design.md`'s AD-13), and returns
rows already shaped for `taller.export.application.csv_zip.build_csv`.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import func
from sqlalchemy.orm import Session

from taller.customers.adapters.models import CustomerModel, VehicleModel
from taller.export.application.csv_zip import CellValue, format_local_timestamp, format_money
from taller.inventory.adapters.models import ItemModel, StockMovementModel
from taller.workorders.adapters.models import PaymentModel, WorkOrderLineModel, WorkOrderModel

CUSTOMERS_HEADERS = [
    "id",
    "full_name",
    "phone",
    "phone_is_mobile",
    "notes",
    "archived_at",
    "created_at",
    "updated_at",
]
VEHICLES_HEADERS = [
    "id",
    "customer_id",
    "vehicle_type",
    "make",
    "model",
    "year",
    "color",
    "plate",
    "notes",
    "archived_at",
    "created_at",
    "updated_at",
]
ITEMS_HEADERS = [
    "id",
    "name",
    "category",
    "unit",
    "min_stock",
    "sale_price_hnl",
    "stock",
    "notes",
    "archived_at",
    "created_at",
    "updated_at",
]
INVENTORY_MOVEMENTS_HEADERS = [
    "id",
    "item_id",
    "kind",
    "quantity",
    "delta",
    "note",
    "order_id",
    "order_line_id",
    "occurred_at",
    "recorded_at",
]
WORK_ORDERS_HEADERS = [
    "id",
    "number",
    "status",
    "customer_id",
    "vehicle_id",
    "complaint",
    "odometer_km",
    "notes",
    "total_hnl",
    "paid_hnl",
    "balance_hnl",
    "created_at",
    "approved_at",
    "started_at",
    "completed_at",
    "delivered_at",
    "cancelled_at",
]
WORK_ORDER_LINES_HEADERS = [
    "id",
    "order_id",
    "kind",
    "item_id",
    "description",
    "quantity",
    "unit_price_hnl",
    "line_total_hnl",
    "removed_at",
    "created_at",
]
PAYMENTS_HEADERS = [
    "id",
    "order_id",
    "amount_hnl",
    "method",
    "note",
    "paid_at",
    "voided_at",
    "void_reason",
]


def _optional_str(value: uuid.UUID | None) -> str | None:
    return str(value) if value is not None else None


def customers_rows(session: Session, workshop_id: uuid.UUID) -> list[Sequence[CellValue]]:
    models = (
        session.query(CustomerModel)
        .filter(CustomerModel.workshop_id == workshop_id)
        .order_by(CustomerModel.created_at, CustomerModel.id)
        .all()
    )
    rows: list[Sequence[CellValue]] = []
    for model in models:
        # Mirrors `Customer.phone_is_mobile` (`taller.customers.domain.entities`,
        # AD-8): `None` with no phone, else the first digit is not `2`. Read
        # directly off the model rather than the domain entity, per AD-1's
        # export.adapters -> models-only dependency.
        phone_is_mobile = None if model.phone is None else model.phone[0] != "2"
        rows.append(
            [
                str(model.id),
                model.full_name,
                model.phone,
                phone_is_mobile,
                model.notes,
                format_local_timestamp(model.archived_at),
                format_local_timestamp(model.created_at),
                format_local_timestamp(model.updated_at),
            ]
        )
    return rows


def vehicles_rows(session: Session, workshop_id: uuid.UUID) -> list[Sequence[CellValue]]:
    models = (
        session.query(VehicleModel)
        .filter(VehicleModel.workshop_id == workshop_id)
        .order_by(VehicleModel.created_at, VehicleModel.id)
        .all()
    )
    return [
        [
            str(model.id),
            str(model.customer_id),
            model.vehicle_type,
            model.make,
            model.model,
            model.year,
            model.color,
            model.plate,
            model.notes,
            format_local_timestamp(model.archived_at),
            format_local_timestamp(model.created_at),
            format_local_timestamp(model.updated_at),
        ]
        for model in models
    ]


def items_rows(session: Session, workshop_id: uuid.UUID) -> list[Sequence[CellValue]]:
    models = (
        session.query(ItemModel)
        .filter(ItemModel.workshop_id == workshop_id)
        .order_by(ItemModel.created_at, ItemModel.id)
        .all()
    )
    return [
        [
            str(model.id),
            model.name,
            model.category,
            model.unit,
            model.min_stock,
            format_money(model.sale_price_cents),
            model.stock,
            model.notes,
            format_local_timestamp(model.archived_at),
            format_local_timestamp(model.created_at),
            format_local_timestamp(model.updated_at),
        ]
        for model in models
    ]


def inventory_movements_rows(session: Session, workshop_id: uuid.UUID) -> list[Sequence[CellValue]]:
    models = (
        session.query(StockMovementModel)
        .filter(StockMovementModel.workshop_id == workshop_id)
        .order_by(StockMovementModel.recorded_at, StockMovementModel.id)
        .all()
    )
    return [
        [
            str(model.id),
            str(model.item_id),
            model.kind,
            model.quantity,
            model.delta,
            model.note,
            _optional_str(model.order_id),
            _optional_str(model.order_line_id),
            format_local_timestamp(model.occurred_at),
            format_local_timestamp(model.recorded_at),
        ]
        for model in models
    ]


def _line_totals_by_order(session: Session, workshop_id: uuid.UUID) -> dict[uuid.UUID, int]:
    """Sum each order's non-removed lines' subtotals (`design.md`'s "Order
    totals are `total = sum(line_total)` over lines not removed")."""
    rows = (
        session.query(
            WorkOrderLineModel.order_id,
            func.sum(WorkOrderLineModel.quantity * WorkOrderLineModel.unit_price_cents),
        )
        .filter(
            WorkOrderLineModel.workshop_id == workshop_id,
            WorkOrderLineModel.removed_at.is_(None),
        )
        .group_by(WorkOrderLineModel.order_id)
        .all()
    )
    return {order_id: int(total) for order_id, total in rows}


def _paid_totals_by_order(session: Session, workshop_id: uuid.UUID) -> dict[uuid.UUID, int]:
    """Sum each order's non-voided payments (voided payments are excluded
    from `paid`, matching the payments spec and the cash summary)."""
    rows = (
        session.query(PaymentModel.order_id, func.sum(PaymentModel.amount_cents))
        .filter(PaymentModel.workshop_id == workshop_id, PaymentModel.voided_at.is_(None))
        .group_by(PaymentModel.order_id)
        .all()
    )
    return {order_id: int(total) for order_id, total in rows}


def work_orders_rows(session: Session, workshop_id: uuid.UUID) -> list[Sequence[CellValue]]:
    models = (
        session.query(WorkOrderModel)
        .filter(WorkOrderModel.workshop_id == workshop_id)
        .order_by(WorkOrderModel.created_at, WorkOrderModel.id)
        .all()
    )
    totals_by_order = _line_totals_by_order(session, workshop_id)
    paid_by_order = _paid_totals_by_order(session, workshop_id)

    rows: list[Sequence[CellValue]] = []
    for model in models:
        total_cents = totals_by_order.get(model.id, 0)
        paid_cents = paid_by_order.get(model.id, 0)
        rows.append(
            [
                str(model.id),
                model.number,
                model.status,
                str(model.customer_id),
                str(model.vehicle_id),
                model.complaint,
                model.odometer_km,
                model.notes,
                format_money(total_cents),
                format_money(paid_cents),
                format_money(total_cents - paid_cents),
                format_local_timestamp(model.created_at),
                format_local_timestamp(model.approved_at),
                format_local_timestamp(model.started_at),
                format_local_timestamp(model.completed_at),
                format_local_timestamp(model.delivered_at),
                format_local_timestamp(model.cancelled_at),
            ]
        )
    return rows


def work_order_lines_rows(session: Session, workshop_id: uuid.UUID) -> list[Sequence[CellValue]]:
    models = (
        session.query(WorkOrderLineModel)
        .filter(WorkOrderLineModel.workshop_id == workshop_id)
        .order_by(WorkOrderLineModel.created_at, WorkOrderLineModel.id)
        .all()
    )
    return [
        [
            str(model.id),
            str(model.order_id),
            model.kind,
            _optional_str(model.item_id),
            model.description,
            model.quantity,
            format_money(model.unit_price_cents),
            format_money(model.quantity * model.unit_price_cents),
            format_local_timestamp(model.removed_at),
            format_local_timestamp(model.created_at),
        ]
        for model in models
    ]


def payments_rows(session: Session, workshop_id: uuid.UUID) -> list[Sequence[CellValue]]:
    """Every payment, voided or not (a voided payment's record is never
    deleted, per the `payments` spec). `voided_at`/`void_reason` mark a
    voided row so it stays reconcilable against `work_orders.csv`'s
    `paid_hnl` and `payments_rows`' own total, both of which exclude voided
    payments (see `_paid_totals_by_order`).
    """
    models = (
        session.query(PaymentModel)
        .filter(PaymentModel.workshop_id == workshop_id)
        .order_by(PaymentModel.paid_at, PaymentModel.id)
        .all()
    )
    return [
        [
            str(model.id),
            str(model.order_id),
            format_money(model.amount_cents),
            model.method,
            model.note,
            format_local_timestamp(model.paid_at),
            format_local_timestamp(model.voided_at),
            model.void_reason,
        ]
        for model in models
    ]

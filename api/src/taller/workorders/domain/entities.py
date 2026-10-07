"""Domain entities for the work-orders feature: orders and their lines."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from taller.workorders.domain.status import WorkOrderStatus


class LineKind(StrEnum):
    """The kind of quote line a work order can carry."""

    labor = "labor"
    inventory_part = "inventory_part"
    external_part = "external_part"


@dataclass(slots=True)
class WorkOrderLine:
    """One quote line on a work order: labor, inventory part, or external
    part.

    `kind` and `item_id` are immutable once created (the `work-orders`
    spec: to change the part, remove the line and add a new one).
    `stock_posted_quantity`/`stock_revision` are the per-line
    reconciliation state `plan_reconciliation` reads and advances
    (`design.md`'s AD-4); they stay `0`/`0` for `labor` and
    `external_part` lines (database-enforced by
    `ck_work_order_lines_stock_only_parts`).
    """

    id: uuid.UUID
    workshop_id: uuid.UUID
    order_id: uuid.UUID
    kind: LineKind
    item_id: uuid.UUID | None
    description: str
    quantity: int
    unit_price_cents: int
    stock_posted_quantity: int
    stock_revision: int
    removed_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class WorkOrder:
    """A work order for one vehicle, numbered per workshop.

    `customer_id` is a snapshot of the vehicle's owner at creation time
    (`design.md`'s AD-12), not a live join: vehicles cannot change owner in
    this change, so it also serves as a filter index for "a customer's
    orders". `lines` includes every line, removed ones too: reconciliation
    needs them to know their stock must return to zero. A response schema
    is responsible for excluding removed lines from what it shows.
    """

    id: uuid.UUID
    workshop_id: uuid.UUID
    number: int
    vehicle_id: uuid.UUID
    customer_id: uuid.UUID
    status: WorkOrderStatus
    complaint: str | None
    odometer_km: int | None
    notes: str | None
    created_by: uuid.UUID
    approved_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    delivered_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    lines: list[WorkOrderLine] = field(default_factory=list)


class PaymentMethod(StrEnum):
    """One of the four wire values the `payments` spec allows. English,
    like every other wire value in this change; `copy.ts` holds the
    Spanish labels ("Efectivo", "Transferencia", "Tarjeta", "Otro").
    """

    cash = "cash"
    transfer = "transfer"
    card = "card"
    other = "other"


@dataclass(slots=True)
class Payment:
    """One payment recorded against a work order, in one of four methods.

    Append-only in spirit: once voided, the record is kept rather than
    deleted (`design.md`'s "Resolved Questions"). `voided_at`/`void_reason`
    are both `None` until voided, and voiding is idempotent -- `voided_at`
    never changes once set. A voided payment is excluded from the order's
    paid total, its balance, and the daily cash summary.
    """

    id: uuid.UUID
    workshop_id: uuid.UUID
    order_id: uuid.UUID
    amount_cents: int
    method: PaymentMethod
    note: str | None
    paid_at: datetime
    voided_at: datetime | None
    void_reason: str | None
    created_by: uuid.UUID
    created_at: datetime


@dataclass(slots=True)
class CashSummaryEntry:
    """One payment as shown in the daily cash summary, with the order
    number it belongs to resolved alongside it.

    Kept separate from `Payment` so the write-side entity never carries a
    read-projection field, mirroring inventory's `MovementHistoryEntry`
    (`design.md`'s AD-12).
    """

    payment: Payment
    order_number: int

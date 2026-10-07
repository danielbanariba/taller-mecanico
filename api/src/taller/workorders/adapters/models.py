"""SQLAlchemy ORM models for work orders, their lines, and the per-workshop
numbering counter.

Only the ORM models land in this slice: the migration needs them mapped on
``Base.metadata`` for ``alembic check``/autogenerate, and the inventory
ledger needs ``work_orders``/``work_order_lines`` as foreign-key targets.
The work-order domain entities and use cases that map onto these models
arrive in phase 2's slice 2 (``design.md``'s "Sequencing inside each
phase").
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from taller.shared.db import Base


class WorkshopCounterModel(Base):
    """A per-workshop, named running counter (e.g. the next order number).

    See ``design.md``'s AD-6 for the ``INSERT ... ON CONFLICT DO UPDATE ...
    RETURNING`` upsert that bumps ``value`` atomically.
    """

    __tablename__ = "workshop_counters"

    workshop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workshops.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(32), primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)


class WorkOrderModel(Base):
    """A work order for one vehicle, numbered per workshop.

    ``number`` is unique per workshop (also used for keyset pagination);
    ``customer_id`` is a snapshot of the vehicle's owner at creation time
    (see ``design.md``'s AD-12), not a live join.
    """

    __tablename__ = "work_orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('quote', 'approved', 'in_progress', 'completed', 'delivered', 'cancelled')",
            name="ck_work_orders_status",
        ),
        CheckConstraint(
            "odometer_km IS NULL OR odometer_km >= 0", name="ck_work_orders_odometer_nonneg"
        ),
        UniqueConstraint("workshop_id", "number", name="uq_work_orders_workshop_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workshops.id"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vehicles.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    odometer_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkOrderLineModel(Base):
    """One quote line (labor, inventory part, or external part) on an order.

    A line's ``kind`` and ``item_id`` are immutable (to change the part,
    remove the line and add a new one). ``stock_posted_quantity``/
    ``stock_revision`` track the per-line reconciliation state from
    ``design.md``'s AD-4, written only by the work-order use cases
    (phase 2's slice 3).
    """

    __tablename__ = "work_order_lines"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('labor', 'inventory_part', 'external_part')",
            name="ck_work_order_lines_kind",
        ),
        CheckConstraint("quantity >= 1 AND quantity <= 10000", name="ck_work_order_lines_quantity"),
        CheckConstraint(
            "unit_price_cents >= 0 AND unit_price_cents <= 1000000000",
            name="ck_work_order_lines_unit_price",
        ),
        CheckConstraint(
            "(kind = 'inventory_part') = (item_id IS NOT NULL)",
            name="ck_work_order_lines_item_matches_kind",
        ),
        CheckConstraint(
            "kind = 'inventory_part' OR (stock_posted_quantity = 0 AND stock_revision = 0)",
            name="ck_work_order_lines_stock_only_parts",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workshops.id"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("work_orders.id"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("inventory_items.id"), nullable=True, index=True
    )
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_posted_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PaymentModel(Base):
    """One payment recorded against a work order (``design.md``'s "Data
    model per phase -> Phase 3").

    ``voided_at``/``void_reason`` support the Resolved-Questions voiding
    feature and are not part of ``design.md``'s original table, which
    predates that resolved question (``tasks.md``'s P3.S1.T3).
    """

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_payments_amount_positive"),
        CheckConstraint(
            "method IN ('cash', 'transfer', 'card', 'other')", name="ck_payments_method"
        ),
        Index("ix_payments_workshop_paid_at", "workshop_id", "paid_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workshops.id"), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("work_orders.id"), nullable=False, index=True
    )
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

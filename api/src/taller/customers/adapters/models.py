"""SQLAlchemy ORM models for customers and their vehicles."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from taller.shared.db import Base


class CustomerModel(Base):
    """A workshop's customer.

    ``billing_name``/``rtn`` are optional fiscal fields (`sar-invoicing`'s
    `customers` delta): the check mirrors `taller.customers.domain.rtn.Rtn`,
    the real guarantee behind the application layer's normalization.
    """

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("rtn IS NULL OR rtn ~ '^[0-9]{14}$'", name="ck_customers_rtn_digits"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workshops.id"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(8), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    billing_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rtn: Mapped[str | None] = mapped_column(String(14), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class VehicleModel(Base):
    """A vehicle owned by one customer.

    The partial unique index enforces "a plate is unique per workshop
    among active vehicles" (AD-9) at the database level, the real
    guarantee behind the application layer's pre-insert check (see
    ``taller.customers.application.use_cases``, slice 2).
    """

    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint(
            "vehicle_type IN ('car', 'motorcycle', 'other')", name="ck_vehicles_vehicle_type"
        ),
        Index(
            "uq_vehicles_workshop_plate_active",
            "workshop_id",
            "plate",
            unique=True,
            postgresql_where=text("archived_at IS NULL AND plate IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workshops.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    vehicle_type: Mapped[str] = mapped_column(String(16), nullable=False)
    make: Mapped[str] = mapped_column(String(60), nullable=False)
    model: Mapped[str | None] = mapped_column(String(60), nullable=True)
    year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    plate: Mapped[str | None] = mapped_column(String(12), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

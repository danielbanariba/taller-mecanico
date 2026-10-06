"""SQLAlchemy ORM models for inventory items and their stock movement ledger."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from taller.shared.db import Base


class ItemModel(Base):
    """A workshop's inventory item.

    ``stock`` is a cache of ``SUM(movements.delta)``; it is only ever
    written by the application layer in the same transaction as a movement
    insert (see ``taller.inventory.application.use_cases``), never derived
    here. Active item names are unique per workshop, case- and
    accent-insensitively, via a partial index created in the migration
    (``archived_at IS NULL``), not expressible as a plain SQLAlchemy
    ``UniqueConstraint``.
    """

    __tablename__ = "inventory_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workshops.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit: Mapped[str] = mapped_column(String(40), nullable=False, server_default="unidad")
    min_stock: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    sale_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StockMovementModel(Base):
    """One append-only entry in an item's stock ledger.

    ``id`` is client-generated (an offline-created UUID), which is what
    makes replaying the same movement idempotent at the application layer;
    see ``taller.inventory.application.use_cases.record_movement``.
    """

    __tablename__ = "inventory_movements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workshops.id"), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inventory_items.id"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

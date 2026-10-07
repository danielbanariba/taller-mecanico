"""Domain entities for the inventory feature: items and stock movements."""

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Item:
    """A workshop's inventory item.

    ``stock`` is a cache of ``SUM(movements.delta)`` for this item, kept
    consistent with the ledger by updating it in the same transaction as
    every movement insert (see ``taller.inventory.application.use_cases``).
    """

    id: uuid.UUID
    workshop_id: uuid.UUID
    name: str
    category: str | None
    unit: str
    min_stock: int
    sale_price_cents: int | None
    notes: str | None
    stock: int
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def needs_review(self) -> bool:
        """True when stock went negative (allowed, never blocked, but flagged)."""
        return self.stock < 0

    @property
    def is_low(self) -> bool:
        """True when a minimum is configured and stock has reached it."""
        return self.min_stock > 0 and self.stock <= self.min_stock


@dataclass(slots=True)
class StockMovement:
    """One append-only entry in an item's stock ledger.

    ``delta`` is computed server-side (see
    ``taller.inventory.domain.stock.compute_delta``) and never supplied by
    the client; ``quantity`` is what the client reported (the amount moved,
    or the physically counted stock for an adjustment).
    """

    id: uuid.UUID
    workshop_id: uuid.UUID
    item_id: uuid.UUID
    kind: str
    quantity: int
    delta: int
    note: str | None
    occurred_at: datetime
    recorded_at: datetime
    created_by: uuid.UUID
    #: Set only when a work-order line caused this movement (see
    #: `design.md`'s AD-3); `None` for manual adjustments, physical counts,
    #: and offline-queued movements.
    order_id: uuid.UUID | None = None
    order_line_id: uuid.UUID | None = None


@dataclass(slots=True)
class MovementHistoryEntry:
    """A movement as shown in an item's history, with the order number it
    belongs to (when linked) resolved alongside it.

    Kept separate from `StockMovement` so the write-side entity never
    carries a read-projection field (see `design.md`'s AD-12).
    """

    movement: StockMovement
    order_number: int | None

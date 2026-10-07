"""Ports the inventory use cases depend on, implemented by adapters."""

import uuid
from typing import Protocol

from taller.inventory.domain.entities import Item, MovementHistoryEntry, StockMovement


class ItemRepository(Protocol):
    def get_by_id(self, *, workshop_id: uuid.UUID, item_id: uuid.UUID) -> Item | None: ...

    def get_for_update(self, *, workshop_id: uuid.UUID, item_id: uuid.UUID) -> Item | None:
        """Like :meth:`get_by_id`, but locks the row (``SELECT ... FOR
        UPDATE``) so the caller can safely read-then-write its stock within
        one transaction.
        """
        ...

    def get_active_by_name(
        self, *, workshop_id: uuid.UUID, name: str, exclude_id: uuid.UUID | None = None
    ) -> Item | None:
        """The active (non-archived) item whose name matches case- and
        accent-insensitively, if any, excluding ``exclude_id`` (used when
        renaming an item to check it does not collide with itself).
        """
        ...

    def add(self, item: Item) -> None: ...

    def save(self, item: Item) -> None:
        """Persist every mutable field of an already-existing item."""
        ...

    def list(
        self,
        *,
        workshop_id: uuid.UUID,
        query: str | None,
        low_stock_only: bool,
        include_archived: bool,
    ) -> list[Item]: ...


class MovementRepository(Protocol):
    def get_by_id(
        self, *, workshop_id: uuid.UUID, movement_id: uuid.UUID
    ) -> StockMovement | None: ...

    def add(self, movement: StockMovement) -> None: ...

    def list_for_item(
        self, *, workshop_id: uuid.UUID, item_id: uuid.UUID, limit: int
    ) -> list[MovementHistoryEntry]: ...

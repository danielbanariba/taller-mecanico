"""Domain errors for the inventory feature (items and stock movements)."""

import uuid


class InvalidItemName(ValueError):
    """Raised when a value cannot be normalized into a valid item name."""

    def __init__(self, raw: str) -> None:
        super().__init__(f"Invalid item name: {raw!r}")
        self.raw = raw


class ItemNotFound(Exception):
    """Raised when an item does not exist in the caller's workshop.

    Also used when the item exists but belongs to another workshop, so
    tenant isolation never leaks whether the item exists at all.
    """

    def __init__(self, item_id: uuid.UUID) -> None:
        super().__init__(f"Item not found: {item_id}")
        self.item_id = item_id


class ItemNameTaken(Exception):
    """Raised when an active item in the workshop already has this name."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Item name already in use: {name}")
        self.name = name


class ItemIdConflict(Exception):
    """Raised when a client-supplied item id exists with different fields."""

    def __init__(self, item_id: uuid.UUID) -> None:
        super().__init__(f"Item id already exists with different fields: {item_id}")
        self.item_id = item_id


class InvalidMovementKind(ValueError):
    """Raised when a movement's kind is not one of in/out/adjust."""

    def __init__(self, kind: str) -> None:
        super().__init__(f"Invalid movement kind: {kind!r}")
        self.kind = kind


class InvalidMovementQuantity(ValueError):
    """Raised when a movement's quantity violates its kind's rule.

    in/out require a positive integer (the thing actually moved); adjust
    requires a non-negative integer (a physically counted stock).
    """

    def __init__(self, *, kind: str, quantity: int) -> None:
        super().__init__(f"Invalid quantity {quantity!r} for movement kind {kind!r}")
        self.kind = kind
        self.quantity = quantity


class MovementIdConflict(Exception):
    """Raised when a client-supplied movement id exists with a different payload."""

    def __init__(self, movement_id: uuid.UUID) -> None:
        super().__init__(f"Movement id already exists with a different payload: {movement_id}")
        self.movement_id = movement_id

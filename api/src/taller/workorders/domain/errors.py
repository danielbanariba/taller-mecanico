"""Domain errors for the work-orders feature."""

import uuid


class WorkOrderNotFound(Exception):
    """Raised when a work order does not exist in the caller's workshop.

    Also used when the order exists but belongs to another workshop, so
    tenant isolation never leaks whether the order exists at all.
    """

    def __init__(self, order_id: uuid.UUID) -> None:
        super().__init__(f"Work order not found: {order_id}")
        self.order_id = order_id


class WorkOrderIdConflict(Exception):
    """Raised when a client-supplied order id exists with different fields."""

    def __init__(self, order_id: uuid.UUID) -> None:
        super().__init__(f"Work order id already exists with different fields: {order_id}")
        self.order_id = order_id


class InvalidStatusTransition(Exception):
    """Raised when a requested status is not reachable from the order's
    current status (per the fixed transition table). Used starting
    Slice 3's `change_status`.
    """

    def __init__(self, *, current: str, target: str) -> None:
        super().__init__(f"Cannot transition from {current!r} to {target!r}")
        self.current = current
        self.target = target


class WorkOrderLocked(Exception):
    """Raised when the order's own fields or its lines are edited once the
    order is `delivered` or `cancelled`.
    """

    def __init__(self, order_id: uuid.UUID) -> None:
        super().__init__(f"Work order is locked: {order_id}")
        self.order_id = order_id


class WorkOrderLineNotFound(Exception):
    """Raised when a line id does not exist on the order, or belongs to
    another order.
    """

    def __init__(self, line_id: uuid.UUID) -> None:
        super().__init__(f"Work order line not found: {line_id}")
        self.line_id = line_id


class WorkOrderLineIdConflict(Exception):
    """Raised when a client-supplied line id exists with different fields."""

    def __init__(self, line_id: uuid.UUID) -> None:
        super().__init__(f"Work order line id already exists with different fields: {line_id}")
        self.line_id = line_id


class ItemNotFoundForLine(Exception):
    """Raised when an inventory-part line references an item id that does
    not exist, belongs to another workshop, or is archived.
    """

    def __init__(self, item_id: uuid.UUID | None) -> None:
        super().__init__(f"Item not found for line: {item_id}")
        self.item_id = item_id

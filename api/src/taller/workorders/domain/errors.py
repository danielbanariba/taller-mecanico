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


class WorkOrderNotPayable(Exception):
    """Raised when a payment is recorded against an order whose status is
    not in `PAYABLE` (`quote` or `cancelled`).
    """

    def __init__(self, order_id: uuid.UUID) -> None:
        super().__init__(f"Work order does not accept payments: {order_id}")
        self.order_id = order_id


class PaymentExceedsBalance(Exception):
    """Raised when a payment's amount is more than the order's current
    balance due, including when the balance is already zero or negative.
    """

    def __init__(self, order_id: uuid.UUID) -> None:
        super().__init__(f"Payment exceeds the order's balance: {order_id}")
        self.order_id = order_id


class WorkOrderHasPayments(Exception):
    """Raised when an order is cancelled while it has one or more
    non-voided payments.
    """

    def __init__(self, order_id: uuid.UUID) -> None:
        super().__init__(f"Work order has non-voided payments: {order_id}")
        self.order_id = order_id


class PaymentIdConflict(Exception):
    """Raised when a client-supplied payment id exists with different
    fields.
    """

    def __init__(self, payment_id: uuid.UUID) -> None:
        super().__init__(f"Payment id already exists with different fields: {payment_id}")
        self.payment_id = payment_id


class PaymentNotFound(Exception):
    """Raised when a payment id does not exist on the target order --
    either nonexistent, or recorded against a different order. Distinct
    from `WorkOrderNotFound`, which covers a missing or cross-workshop
    order id. Not present in `specs/payments/spec.md` (a spec delta: see
    `tasks.md`'s P3.S1.T1).
    """

    def __init__(self, payment_id: uuid.UUID) -> None:
        super().__init__(f"Payment not found: {payment_id}")
        self.payment_id = payment_id


class WorkOrderInvoiced(Exception):
    """Raised when a line is added, edited or removed on an order that
    has a non-credited Factura (`design.md`'s AD-2). Distinct from
    `WorkOrderLocked`: a `completed` order with an active invoice is
    still editable by status, but its lines are frozen because a fiscal
    document already snapshotted them.
    """

    def __init__(self, order_id: uuid.UUID) -> None:
        super().__init__(f"Work order has an active Factura: {order_id}")
        self.order_id = order_id

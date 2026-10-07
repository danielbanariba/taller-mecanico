"""Pure stock-delta computation: the arithmetic a movement applies to stock.

Kept free of any persistence or framework concerns so it can be unit tested
directly, and reused identically by every caller (the HTTP schema layer, for
early validation, and the application layer, which actually applies it).
"""

from taller.inventory.domain.errors import InvalidMovementKind, InvalidMovementQuantity

IN = "in"
OUT = "out"
ADJUST = "adjust"

#: The only valid movement kinds. Kept in sync with the HTTP schema's
#: ``Literal["in", "out", "adjust"]`` and the ``inventory_movements.kind``
#: column.
MOVEMENT_KINDS = frozenset({IN, OUT, ADJUST})

#: Upper bound on a single movement's quantity (and, by extension, on
#: `initial_stock`, which is recorded as an `adjust` movement). Keeps a
#: client-supplied value from ever reaching the database as an uncontrolled
#: integer, and keeps the application layer safe even when a caller bypasses
#: the HTTP schema layer (see `taller.inventory.adapters.schemas`, which
#: enforces the same bound at the 422 level).
MAX_QUANTITY = 1_000_000

#: Bounds of PostgreSQL's `integer` column type, which backs
#: `inventory_items.stock`. A movement whose resulting stock would not fit
#: here must be rejected before it reaches the database (see
#: `is_stock_in_range` and `taller.inventory.application.use_cases.record_movement`).
INT32_MIN = -2_147_483_648
INT32_MAX = 2_147_483_647


def validate_quantity(*, kind: str, quantity: int) -> None:
    """Validate a movement's declared quantity against its kind's rule.

    Raises:
        InvalidMovementKind: ``kind`` is not one of :data:`MOVEMENT_KINDS`.
        InvalidMovementQuantity: the quantity violates its kind's rule.
    """
    if kind in (IN, OUT):
        if quantity <= 0 or quantity > MAX_QUANTITY:
            raise InvalidMovementQuantity(kind=kind, quantity=quantity)
    elif kind == ADJUST:
        if quantity < 0 or quantity > MAX_QUANTITY:
            raise InvalidMovementQuantity(kind=kind, quantity=quantity)
    else:
        raise InvalidMovementKind(kind)


def is_stock_in_range(stock: int) -> bool:
    """True when ``stock`` fits PostgreSQL's `integer` column type."""
    return INT32_MIN <= stock <= INT32_MAX


def compute_delta(*, kind: str, quantity: int, current_stock: int) -> int:
    """Compute the signed change a movement applies to stock.

    - ``in``: adds ``quantity`` (must be a positive integer).
    - ``out``: subtracts ``quantity`` (must be a positive integer).
    - ``adjust``: ``quantity`` is the physically counted stock (must be
      zero or positive); the delta is the difference against
      ``current_stock`` at the moment the server applies it.

    Raises:
        InvalidMovementKind: ``kind`` is not one of :data:`MOVEMENT_KINDS`.
        InvalidMovementQuantity: the quantity violates its kind's rule.
    """
    validate_quantity(kind=kind, quantity=quantity)
    if kind == IN:
        return quantity
    if kind == OUT:
        return -quantity
    return quantity - current_stock

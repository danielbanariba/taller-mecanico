"""Money helpers for work orders: integer cents only, no floats (AD-10)."""

from taller.workorders.domain.entities import WorkOrderLine


def line_subtotal_cents(line: WorkOrderLine) -> int:
    """A line's subtotal: its quantity times its unit price, in cents."""
    return line.quantity * line.unit_price_cents


def order_total_cents(lines: list[WorkOrderLine]) -> int:
    """An order's total: the sum of every non-removed line's subtotal.

    No tax computation or breakdown anywhere (line prices are final
    amounts, per the `work-orders` spec).
    """
    return sum(line_subtotal_cents(line) for line in lines if line.removed_at is None)

"""Money helpers for work orders: integer cents only, no floats (AD-10)."""

from collections.abc import Sequence

from taller.workorders.domain.entities import Payment, WorkOrderLine


def line_subtotal_cents(line: WorkOrderLine) -> int:
    """A line's subtotal: its quantity times its unit price, in cents."""
    return line.quantity * line.unit_price_cents


def order_total_cents(lines: list[WorkOrderLine]) -> int:
    """An order's total: the sum of every non-removed line's subtotal.

    No tax computation or breakdown anywhere (line prices are final
    amounts, per the `work-orders` spec).
    """
    return sum(line_subtotal_cents(line) for line in lines if line.removed_at is None)


def paid_cents(payments: Sequence[Payment]) -> int:
    """An order's paid total: the sum of its non-voided payments' amounts.

    A voided payment never contributes (the `payments` spec's "An Order's
    Paid Total And Balance Due Reflect Only Its Non-Voided Recorded
    Payments").
    """
    return sum(payment.amount_cents for payment in payments if payment.voided_at is None)


def balance_cents(lines: Sequence[WorkOrderLine], payments: Sequence[Payment]) -> int:
    """An order's balance due: its total minus its paid total.

    Can go negative ("Saldo a favor", shown by the web) if a line edit
    lowers the total below what is already paid; money is never moved
    automatically (`design.md`'s AD-11).
    """
    return order_total_cents(list(lines)) - paid_cents(payments)

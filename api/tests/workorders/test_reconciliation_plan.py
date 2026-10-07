"""Tests for `plan_reconciliation`, the pure function that decides which
inventory movements a work order's current line state requires (AD-4).

No database: every input is built in memory.
"""

import uuid
from datetime import UTC, datetime

from taller.workorders.domain.entities import LineKind, WorkOrderLine
from taller.workorders.domain.status import WorkOrderStatus
from taller.workorders.domain.stock import movement_id_for, plan_reconciliation

_ORDER_ID = uuid.uuid4()
_WORKSHOP_ID = uuid.uuid4()
_NOW = datetime.now(UTC)


def _line(
    *,
    line_id: uuid.UUID | None = None,
    item_id: uuid.UUID | None = None,
    kind: LineKind = LineKind.inventory_part,
    quantity: int = 1,
    stock_posted_quantity: int = 0,
    stock_revision: int = 0,
    removed_at: datetime | None = None,
) -> WorkOrderLine:
    return WorkOrderLine(
        id=line_id or uuid.uuid4(),
        workshop_id=_WORKSHOP_ID,
        order_id=_ORDER_ID,
        kind=kind,
        item_id=item_id if kind == LineKind.inventory_part else None,
        description="Pastillas de freno",
        quantity=quantity,
        unit_price_cents=50000,
        stock_posted_quantity=stock_posted_quantity,
        stock_revision=stock_revision,
        removed_at=removed_at,
        created_at=_NOW,
        updated_at=_NOW,
    )


def test_a_not_yet_posted_part_line_plans_its_initial_consumption() -> None:
    """Defect this catches: the initial consumption is skipped, or posts
    the wrong quantity, when the order enters `in_progress`.
    """
    item_id = uuid.uuid4()
    line = _line(item_id=item_id, quantity=3)

    plan = plan_reconciliation(_ORDER_ID, WorkOrderStatus.in_progress, [line])

    assert len(plan) == 1
    planned = plan[0]
    assert planned.line_id == line.id
    assert planned.item_id == item_id
    assert planned.kind == "out"
    assert planned.quantity == 3
    assert planned.new_posted == 3
    assert planned.new_revision == 1
    assert planned.movement_id == movement_id_for(_ORDER_ID, line.id, 1)


def test_increasing_quantity_while_consuming_plans_only_the_delta() -> None:
    """Defect this catches: an edit re-posts the line's full new quantity
    instead of only the delta, double-counting consumption.
    """
    item_id = uuid.uuid4()
    line = _line(item_id=item_id, quantity=5, stock_posted_quantity=2, stock_revision=1)

    plan = plan_reconciliation(_ORDER_ID, WorkOrderStatus.in_progress, [line])

    assert len(plan) == 1
    assert plan[0].kind == "out"
    assert plan[0].quantity == 3
    assert plan[0].new_posted == 5
    assert plan[0].new_revision == 2


def test_decreasing_quantity_while_consuming_plans_an_in_delta() -> None:
    """Defect this catches: an edit that lowers quantity does not return
    the freed units to stock.
    """
    item_id = uuid.uuid4()
    line = _line(item_id=item_id, quantity=2, stock_posted_quantity=5, stock_revision=1)

    plan = plan_reconciliation(_ORDER_ID, WorkOrderStatus.in_progress, [line])

    assert len(plan) == 1
    assert plan[0].kind == "in"
    assert plan[0].quantity == 3
    assert plan[0].new_posted == 2
    assert plan[0].new_revision == 2


def test_a_removed_line_plans_returning_its_posted_quantity() -> None:
    """Defect this catches: removing a consuming line leaves its stock
    taken, because the plan only looks at `quantity`, not `removed_at`.
    """
    item_id = uuid.uuid4()
    line = _line(
        item_id=item_id, quantity=4, stock_posted_quantity=4, stock_revision=1, removed_at=_NOW
    )

    plan = plan_reconciliation(_ORDER_ID, WorkOrderStatus.in_progress, [line])

    assert len(plan) == 1
    assert plan[0].kind == "in"
    assert plan[0].quantity == 4
    assert plan[0].new_posted == 0


def test_cancelling_reverses_every_previously_posted_line_only() -> None:
    """Defect this catches: cancellation reverses only some lines, or
    reverses a line that never consumed (posted 0).
    """
    item_a = uuid.uuid4()
    item_b = uuid.uuid4()
    consumed = _line(item_id=item_a, quantity=5, stock_posted_quantity=5, stock_revision=1)
    never_consumed = _line(item_id=item_b, quantity=2, stock_posted_quantity=0, stock_revision=0)

    plan = plan_reconciliation(_ORDER_ID, WorkOrderStatus.cancelled, [consumed, never_consumed])

    assert len(plan) == 1
    assert plan[0].line_id == consumed.id
    assert plan[0].kind == "in"
    assert plan[0].quantity == 5


def test_labor_and_external_part_lines_never_appear_in_the_plan() -> None:
    """Defect this catches: a non-part line accidentally touches stock."""
    labor = _line(kind=LineKind.labor, quantity=1)
    external = _line(kind=LineKind.external_part, quantity=1)

    for target_status in (
        WorkOrderStatus.quote,
        WorkOrderStatus.approved,
        WorkOrderStatus.in_progress,
        WorkOrderStatus.completed,
        WorkOrderStatus.delivered,
        WorkOrderStatus.cancelled,
    ):
        assert plan_reconciliation(_ORDER_ID, target_status, [labor, external]) == []


def test_the_plan_is_sorted_by_item_then_line_id() -> None:
    """Defect this catches: an unsorted plan, which is the deadlock AD-5's
    lock order exists to prevent.
    """
    item_low = uuid.UUID(int=1)
    item_high = uuid.UUID(int=2)
    line_for_high_item = _line(line_id=uuid.UUID(int=10), item_id=item_high, quantity=1)
    line_for_low_item = _line(line_id=uuid.UUID(int=20), item_id=item_low, quantity=1)

    plan = plan_reconciliation(
        _ORDER_ID, WorkOrderStatus.in_progress, [line_for_high_item, line_for_low_item]
    )

    assert [planned.item_id for planned in plan] == [item_low, item_high]

"""Pure stock-reconciliation planning for work orders (`design.md`'s
AD-4/AD-5).

`plan_reconciliation` is the one function every status-changing or
line-changing use case runs to decide what inventory movements a work
order's current line state requires. It never touches the database; the
work-orders application layer posts the plan's movements through
inventory's `record_movement` (AD-2).
"""

import uuid
from dataclasses import dataclass
from typing import Literal, cast

from taller.workorders.domain.entities import LineKind, WorkOrderLine
from taller.workorders.domain.status import CONSUMING, WorkOrderStatus

#: Fixed namespace for every work-order stock-consumption movement id,
#: mirroring `taller.inventory.application.use_cases._INITIAL_STOCK_NAMESPACE`:
#: a pure function of a constant input, so it is identical across every
#: process and run, and never needs to be hand-picked or stored anywhere.
WORK_ORDER_STOCK_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_URL, "https://taller-mecanico.invalid/workorders/stock-consumption"
)


def movement_id_for(order_id: uuid.UUID, line_id: uuid.UUID, revision: int) -> uuid.UUID:
    """Deterministic movement id for one line's posting event (the
    `work-order-stock-consumption` spec's `order:line:revision` idiom):
    retrying consumption, an edit, or a reversal with the same inputs
    resolves to the same id, and therefore the same replay, never a
    second movement.
    """
    return uuid.uuid5(WORK_ORDER_STOCK_NAMESPACE, f"{order_id}:{line_id}:{revision}")


@dataclass(frozen=True, slots=True)
class PlannedMovement:
    """One inventory movement `plan_reconciliation` says must be posted."""

    line_id: uuid.UUID
    item_id: uuid.UUID
    movement_id: uuid.UUID
    kind: Literal["in", "out"]
    quantity: int
    new_posted: int
    new_revision: int


def plan_reconciliation(
    order_id: uuid.UUID, status: WorkOrderStatus, lines: list[WorkOrderLine]
) -> list[PlannedMovement]:
    """Plan the movements needed to reconcile every inventory-part line's
    `stock_posted_quantity` toward its target for `status` (AD-4):
    `line.quantity` while the line is an active inventory part and
    `status` is in `CONSUMING`, otherwise `0`.

    Pure and deterministic: the same inputs always produce the same plan,
    sorted by `(item_id, line_id)` -- AD-5's lock order, so two concurrent
    plans over overlapping items never lock them out of order and
    deadlock.

    Labor and external-part lines never appear in the plan: their target
    is always `0`, and their posted quantity never moves from `0`
    (database-enforced by `ck_work_order_lines_stock_only_parts`), so they
    never have a `target != posted` difference to plan for.
    """
    planned: list[PlannedMovement] = []
    for line in lines:
        target = (
            line.quantity
            if line.kind == LineKind.inventory_part
            and line.removed_at is None
            and status in CONSUMING
            else 0
        )
        if target == line.stock_posted_quantity:
            continue
        diff = target - line.stock_posted_quantity
        revision = line.stock_revision + 1
        planned.append(
            PlannedMovement(
                line_id=line.id,
                # `ck_work_order_lines_item_matches_kind` guarantees an
                # `inventory_part` line always has an `item_id`, and only
                # those lines ever reach a nonzero target above.
                item_id=cast(uuid.UUID, line.item_id),
                movement_id=movement_id_for(order_id, line.id, revision),
                kind="out" if diff > 0 else "in",
                quantity=abs(diff),
                new_posted=target,
                new_revision=revision,
            )
        )
    planned.sort(key=lambda planned_movement: (planned_movement.item_id, planned_movement.line_id))
    return planned

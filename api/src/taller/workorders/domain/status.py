"""Work-order status machine: six fixed states, no back edges (AD-7).

Wire values are English (the `work-orders` spec's wire format); `copy.ts`
on the web side shows the Spanish labels.
"""

from enum import StrEnum
from types import MappingProxyType
from typing import Final


class WorkOrderStatus(StrEnum):
    quote = "quote"
    approved = "approved"
    in_progress = "in_progress"
    completed = "completed"
    delivered = "delivered"
    cancelled = "cancelled"


#: The acyclic transition table from the `work-orders` spec. No status can
#: ever be re-entered: a stale or duplicate request for "-> X" is either a
#: no-op (the order is already at X) or a 409 (X is unreachable from the
#: current status). See `design.md`'s AD-7.
TRANSITIONS: Final[MappingProxyType[WorkOrderStatus, frozenset[WorkOrderStatus]]] = (
    MappingProxyType(
        {
            WorkOrderStatus.quote: frozenset({WorkOrderStatus.approved, WorkOrderStatus.cancelled}),
            WorkOrderStatus.approved: frozenset(
                {WorkOrderStatus.in_progress, WorkOrderStatus.cancelled}
            ),
            WorkOrderStatus.in_progress: frozenset(
                {WorkOrderStatus.completed, WorkOrderStatus.cancelled}
            ),
            WorkOrderStatus.completed: frozenset({WorkOrderStatus.delivered}),
            WorkOrderStatus.delivered: frozenset(),
            WorkOrderStatus.cancelled: frozenset(),
        }
    )
)

#: Statuses in which an inventory-part line's reconciliation target is its
#: full quantity (`design.md`'s AD-4). `approved -> in_progress` is the
#: only transition that enters this set from outside it; `in_progress ->
#: cancelled` is the only one that leaves it.
CONSUMING: Final[frozenset[WorkOrderStatus]] = frozenset(
    {WorkOrderStatus.in_progress, WorkOrderStatus.completed, WorkOrderStatus.delivered}
)

#: Statuses in which the order's own fields and its lines may still be
#: edited. `delivered` and `cancelled` are locked (the `work-orders` spec's
#: line-lock requirement). `PAYABLE` is added in phase 3.
EDITABLE: Final[frozenset[WorkOrderStatus]] = frozenset(
    {
        WorkOrderStatus.quote,
        WorkOrderStatus.approved,
        WorkOrderStatus.in_progress,
        WorkOrderStatus.completed,
    }
)

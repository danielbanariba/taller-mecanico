"""Ports the work-orders use cases depend on, implemented by adapters."""

import uuid
from collections.abc import Sequence
from typing import Protocol

from taller.workorders.domain.entities import WorkOrder
from taller.workorders.domain.status import WorkOrderStatus


class WorkshopCounterRepository(Protocol):
    def next_value(self, *, workshop_id: uuid.UUID, name: str) -> int:
        """Atomically bump and return the named counter's new value.

        An ``INSERT ... ON CONFLICT DO UPDATE ... RETURNING`` upsert
        (``design.md``'s AD-6): no counter row has to exist beforehand, and
        the row lock is held implicitly by the single statement until the
        caller's transaction commits or rolls back.
        """
        ...


class WorkOrderRepository(Protocol):
    def get_by_id(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> WorkOrder | None: ...

    def get_for_update(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> WorkOrder | None:
        """Like :meth:`get_by_id`, but locks the order row (``SELECT ...
        FOR UPDATE``). Every mutating work-order use case starts here
        (``design.md``'s AD-5, lock order step 1), which also serializes
        line edits against status changes.
        """
        ...

    def add(self, order: WorkOrder) -> None:
        """Persist a brand-new order together with its lines, if any."""
        ...

    def save(self, order: WorkOrder) -> None:
        """Persist every mutable field of an already-existing order, and
        reconcile its ``lines`` collection: a line id not yet in the
        database is inserted, and an existing one is updated in place.
        Lines are never deleted (the ``work-orders`` spec's soft-removal
        rule).
        """
        ...

    def list(
        self,
        *,
        workshop_id: uuid.UUID,
        statuses: frozenset[WorkOrderStatus] | None,
        vehicle_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
        before_number: int | None,
        limit: int,
    ) -> list[WorkOrder]:
        """Newest ``number`` first. Returned orders carry no lines; a
        caller needing totals uses :meth:`totals` instead of loading every
        order's lines.
        """
        ...

    def totals(
        self, *, workshop_id: uuid.UUID, order_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        """Each order's total in cents (the sum of its non-removed lines'
        subtotals), batched for a list of summaries.
        """
        ...

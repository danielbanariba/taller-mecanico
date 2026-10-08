"""Ports the work-orders use cases depend on, implemented by adapters."""

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from taller.workorders.domain.entities import InvoiceRef, Payment, WorkOrder
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

    def numbers(
        self, *, workshop_id: uuid.UUID, order_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        """Each order's `number`, batched for the daily cash summary's
        listed payments (phase 3 slice 2). Omits an id with no match.
        """
        ...

    def active_invoice(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> InvoiceRef | None:
        """The order's non-credited Factura, if it has one.

        Reads `fiscal_invoices` by table name only (`design.md`'s
        AD-1/AD-12): `work-orders` never imports the `invoicing` feature.
        """
        ...


class PaymentRepository(Protocol):
    def get_by_id(
        self, *, workshop_id: uuid.UUID, order_id: uuid.UUID, payment_id: uuid.UUID
    ) -> Payment | None:
        """Scoped by `(workshop_id, order_id, payment_id)` together, so a
        payment id that exists but belongs to a different order (or a
        different workshop) is a clean miss, never a cross-order or
        cross-tenant leak.
        """
        ...

    def add(self, payment: Payment) -> None:
        """Persist a brand-new payment."""
        ...

    def save(self, payment: Payment) -> None:
        """Persist a payment's mutable fields (`voided_at`, `void_reason`
        -- every other field is immutable after creation)."""
        ...

    def list_for_order(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> list[Payment]:
        """Every payment recorded against this order, voided or not. A
        caller computing a total or a balance filters for non-voided ones
        itself (`taller.workorders.domain.money.paid_cents`/
        `balance_cents`).
        """
        ...

    def list_for_workshop_day(
        self, *, workshop_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[Payment]:
        """Every payment with `paid_at` in `[start, end)`, for the daily
        cash summary (phase 3 slice 2).
        """
        ...

"""Use cases for the work-orders feature: orders, numbering, quote lines,
and the status machine's stock reconciliation.

``change_status`` and the reconciliation extension to ``add_line``/
``update_line``/``remove_line`` are this feature's one cross-feature call
into inventory's ``record_movement`` (``design.md``'s AD-2): every line
whose reconciliation target differs from its posted quantity posts through
that existing ledger use case, sharing the caller's transaction, so a
status/line change and its movements commit or roll back together.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Final, Literal
from zoneinfo import ZoneInfo

from taller.customers.application.ports import VehicleRepository
from taller.customers.application.use_cases import get_active_vehicle
from taller.identity.application.ports import Clock
from taller.inventory.application.ports import ItemRepository, MovementRepository
from taller.inventory.application.use_cases import record_movement
from taller.workorders.application.ports import (
    PaymentRepository,
    WorkOrderRepository,
    WorkshopCounterRepository,
)
from taller.workorders.domain.entities import (
    CashSummaryEntry,
    LineKind,
    Payment,
    PaymentMethod,
    WorkOrder,
    WorkOrderLine,
)
from taller.workorders.domain.errors import (
    InvalidStatusTransition,
    ItemNotFoundForLine,
    PaymentExceedsBalance,
    PaymentIdConflict,
    PaymentNotFound,
    WorkOrderHasPayments,
    WorkOrderIdConflict,
    WorkOrderLineIdConflict,
    WorkOrderLineNotFound,
    WorkOrderLocked,
    WorkOrderNotFound,
    WorkOrderNotPayable,
)
from taller.workorders.domain.money import balance_cents
from taller.workorders.domain.status import (
    CONSUMING,
    EDITABLE,
    PAYABLE,
    TRANSITIONS,
    WorkOrderStatus,
)
from taller.workorders.domain.stock import plan_reconciliation

#: The fixed day boundary for the daily cash summary (`design.md`'s
#: AD-20): there is no per-workshop time zone setting, so every workshop's
#: "today" is Honduras' own calendar day, regardless of server or client
#: time zone.
HONDURAS_TZ: Final = ZoneInfo("America/Tegucigalpa")

#: The named counter `create_work_order` bumps for every new order
#: (`design.md`'s AD-6). One counter per workshop, keyed by this name.
ORDER_COUNTER_NAME = "work_order"

#: `GET /work-orders`'s `limit` query parameter is capped at this value
#: regardless of what the caller asks for.
MAX_LIST_LIMIT = 100

#: The order field that records when each status was entered (`design.md`'s
#: "Data model per phase -> Phase 2" table). `quote` is unreachable as a
#: target (no edge in `TRANSITIONS` leads into it), so it has no entry.
_STATUS_TIMESTAMP_FIELD: Final[dict[WorkOrderStatus, str]] = {
    WorkOrderStatus.approved: "approved_at",
    WorkOrderStatus.in_progress: "started_at",
    WorkOrderStatus.completed: "completed_at",
    WorkOrderStatus.delivered: "delivered_at",
    WorkOrderStatus.cancelled: "cancelled_at",
}

_OPEN_STATUSES = frozenset(
    {
        WorkOrderStatus.quote,
        WorkOrderStatus.approved,
        WorkOrderStatus.in_progress,
        WorkOrderStatus.completed,
    }
)
_CLOSED_STATUSES = frozenset({WorkOrderStatus.delivered, WorkOrderStatus.cancelled})


def _normalize_optional_text(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip()
    return cleaned or None


def _order_fields_match(
    order: WorkOrder,
    *,
    vehicle_id: uuid.UUID,
    complaint: str | None,
    odometer_km: int | None,
    notes: str | None,
) -> bool:
    return (
        order.vehicle_id == vehicle_id
        and order.complaint == complaint
        and order.odometer_km == odometer_km
        and order.notes == notes
    )


def _find_line(order: WorkOrder, line_id: uuid.UUID) -> WorkOrderLine | None:
    for line in order.lines:
        if line.id == line_id:
            return line
    return None


def _payment_fields_match(
    payment: Payment, *, amount_cents: int, method: PaymentMethod, note: str | None
) -> bool:
    return (
        payment.amount_cents == amount_cents and payment.method == method and payment.note == note
    )


def _line_fields_match(
    line: WorkOrderLine,
    *,
    kind: LineKind,
    item_id: uuid.UUID | None,
    description: str,
    quantity: int,
    unit_price_cents: int,
) -> bool:
    return (
        line.kind == kind
        and line.item_id == item_id
        and line.description == description
        and line.quantity == quantity
        and line.unit_price_cents == unit_price_cents
    )


def _reconcile_stock(
    order: WorkOrder,
    *,
    status: WorkOrderStatus,
    now: datetime,
    created_by: uuid.UUID,
    item_repo: ItemRepository,
    movement_repo: MovementRepository,
) -> None:
    """Run `plan_reconciliation` for `status` against `order.lines`, and
    post every planned movement through inventory's `record_movement`
    (`design.md`'s AD-2), sharing the caller's transaction so a failure
    partway through rolls back everything already posted by this call.

    Advances each affected line's `stock_posted_quantity`/`stock_revision`
    in place (AD-4's invariant); the caller still has to persist the order
    (and its lines) afterward. `status` is passed explicitly rather than
    read from `order.status`, because `change_status` must plan against
    the *target* status before the order's own status field is updated.
    """
    plan = plan_reconciliation(order.id, status, order.lines)
    lines_by_id = {line.id: line for line in order.lines}
    for planned in plan:
        record_movement(
            workshop_id=order.workshop_id,
            movement_id=planned.movement_id,
            item_id=planned.item_id,
            kind=planned.kind,
            quantity=planned.quantity,
            note=None,
            occurred_at=now,
            created_by=created_by,
            item_repo=item_repo,
            movement_repo=movement_repo,
            order_id=order.id,
            order_line_id=planned.line_id,
        )
        line = lines_by_id[planned.line_id]
        line.stock_posted_quantity = planned.new_posted
        line.stock_revision = planned.new_revision
        line.updated_at = now


def change_status(
    *,
    workshop_id: uuid.UUID,
    order_id: uuid.UUID,
    target: WorkOrderStatus,
    created_by: uuid.UUID,
    order_repo: WorkOrderRepository,
    item_repo: ItemRepository,
    movement_repo: MovementRepository,
    payment_repo: PaymentRepository,
) -> WorkOrder:
    """Idempotently `PUT` the order's status to `target` (`design.md`'s
    AD-7, over the acyclic machine in `taller.workorders.domain.status`).

    Locks the order row first (AD-5's lock order, step 1), which also
    serializes this transition against a concurrent line edit or payment.
    A same-status request is a no-op; a `target` unreachable from the
    order's current status raises `InvalidStatusTransition`. Cancelling an
    order with one or more non-voided payments raises `WorkOrderHasPayments`
    (phase 3's guard, `design.md`'s AD-11 and the `payments` spec's "Cancelling
    An Order Counts Only Its Non-Voided Payments"). Otherwise this runs the
    same `plan_reconciliation` call every status/line change finishes with
    (AD-4) -- planned against `target`, before the order's own status field
    moves -- then advances the status and the matching timestamp.

    Raises:
        WorkOrderNotFound: no such order in this workshop.
        InvalidStatusTransition: `target` is not in
            `TRANSITIONS[order.status]`.
        WorkOrderHasPayments: `target` is `cancelled` and the order has at
            least one non-voided payment.
        MovementIdConflict / StockOutOfRange: re-raised unchanged from
            `record_movement` (a movement id planted by a client, or a
            resulting stock outside PostgreSQL's `integer` range).
    """
    order = order_repo.get_for_update(workshop_id=workshop_id, order_id=order_id)
    if order is None:
        raise WorkOrderNotFound(order_id)

    if order.status == target:
        return order
    if target not in TRANSITIONS[order.status]:
        raise InvalidStatusTransition(current=order.status.value, target=target.value)

    if target == WorkOrderStatus.cancelled:
        payments = payment_repo.list_for_order(workshop_id=workshop_id, order_id=order_id)
        if any(payment.voided_at is None for payment in payments):
            raise WorkOrderHasPayments(order_id)

    now = datetime.now(UTC)
    _reconcile_stock(
        order,
        status=target,
        now=now,
        created_by=created_by,
        item_repo=item_repo,
        movement_repo=movement_repo,
    )

    order.status = target
    setattr(order, _STATUS_TIMESTAMP_FIELD[target], now)
    order.updated_at = now
    order_repo.save(order)
    return order


def create_work_order(
    *,
    workshop_id: uuid.UUID,
    order_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    complaint: str | None,
    odometer_km: int | None,
    notes: str | None,
    created_by: uuid.UUID,
    order_repo: WorkOrderRepository,
    counter_repo: WorkshopCounterRepository,
    vehicle_repo: VehicleRepository,
) -> tuple[WorkOrder, bool]:
    """Create a work order, or replay an idempotent create.

    Follows ``design.md``'s AD-6 exact sequencing: replay check first (the
    counter is never touched on a replay), then resolve the vehicle, then
    bump the counter, then insert. The route retries this once on a
    ``work_orders_pkey`` ``IntegrityError`` (two concurrent creates with
    the same id): the rollback that follows also undoes the counter bump,
    so a retry never skips a number.

    Raises:
        VehicleNotFound: no active vehicle ``vehicle_id`` in this
            workshop (``taller.customers.domain.errors.VehicleNotFound``,
            raised by ``get_active_vehicle``).
        WorkOrderIdConflict: ``order_id`` already exists with different
            fields.
    """
    normalized_complaint = _normalize_optional_text(complaint)
    normalized_notes = _normalize_optional_text(notes)

    existing = order_repo.get_by_id(workshop_id=workshop_id, order_id=order_id)
    if existing is not None:
        if not _order_fields_match(
            existing,
            vehicle_id=vehicle_id,
            complaint=normalized_complaint,
            odometer_km=odometer_km,
            notes=normalized_notes,
        ):
            raise WorkOrderIdConflict(order_id)
        return existing, False

    vehicle = get_active_vehicle(
        workshop_id=workshop_id, vehicle_id=vehicle_id, vehicle_repo=vehicle_repo
    )

    number = counter_repo.next_value(workshop_id=workshop_id, name=ORDER_COUNTER_NAME)

    now = datetime.now(UTC)
    order = WorkOrder(
        id=order_id,
        workshop_id=workshop_id,
        number=number,
        vehicle_id=vehicle.id,
        customer_id=vehicle.customer_id,
        status=WorkOrderStatus.quote,
        complaint=normalized_complaint,
        odometer_km=odometer_km,
        notes=normalized_notes,
        created_by=created_by,
        approved_at=None,
        started_at=None,
        completed_at=None,
        delivered_at=None,
        cancelled_at=None,
        created_at=now,
        updated_at=now,
        lines=[],
    )
    order_repo.add(order)
    return order, True


def get_work_order(
    *, workshop_id: uuid.UUID, order_id: uuid.UUID, order_repo: WorkOrderRepository
) -> WorkOrder:
    """Raises: WorkOrderNotFound: no such work order in this workshop."""
    order = order_repo.get_by_id(workshop_id=workshop_id, order_id=order_id)
    if order is None:
        raise WorkOrderNotFound(order_id)
    return order


def list_work_orders(
    *,
    workshop_id: uuid.UUID,
    status_group: Literal["open", "closed", "all"],
    vehicle_id: uuid.UUID | None,
    customer_id: uuid.UUID | None,
    before_number: int | None,
    limit: int,
    order_repo: WorkOrderRepository,
) -> list[WorkOrder]:
    """``status_group``: ``"open"`` (``quote``, ``approved``,
    ``in_progress``, ``completed``), ``"closed"`` (``delivered``,
    ``cancelled``), or ``"all"``. ``limit`` is capped at
    :data:`MAX_LIST_LIMIT` regardless of what the caller asks for.
    """
    statuses: frozenset[WorkOrderStatus] | None
    if status_group == "open":
        statuses = _OPEN_STATUSES
    elif status_group == "closed":
        statuses = _CLOSED_STATUSES
    else:
        statuses = None
    return order_repo.list(
        workshop_id=workshop_id,
        statuses=statuses,
        vehicle_id=vehicle_id,
        customer_id=customer_id,
        before_number=before_number,
        limit=min(limit, MAX_LIST_LIMIT),
    )


def update_work_order(
    *, workshop_id: uuid.UUID, order_id: uuid.UUID, fields: dict, order_repo: WorkOrderRepository
) -> WorkOrder:
    """Edit the order's own fields (``complaint``, ``odometer_km``,
    ``notes``).

    Locks the order row first (``design.md``'s AD-5), like every other
    mutating work-order use case: a blind read-then-save here would
    otherwise be able to overwrite a concurrently committed status
    transition or line edit with this call's own stale snapshot.

    Raises:
        WorkOrderNotFound: no such order in this workshop.
        WorkOrderLocked: the order's status is ``delivered`` or
            ``cancelled``.
    """
    order = order_repo.get_for_update(workshop_id=workshop_id, order_id=order_id)
    if order is None:
        raise WorkOrderNotFound(order_id)
    if order.status not in EDITABLE:
        raise WorkOrderLocked(order_id)

    if "complaint" in fields:
        order.complaint = _normalize_optional_text(fields["complaint"])
    if "odometer_km" in fields:
        order.odometer_km = fields["odometer_km"]
    if "notes" in fields:
        order.notes = _normalize_optional_text(fields["notes"])

    order.updated_at = datetime.now(UTC)
    order_repo.save(order)
    return order


def add_line(
    *,
    workshop_id: uuid.UUID,
    order_id: uuid.UUID,
    line_id: uuid.UUID,
    kind: LineKind,
    item_id: uuid.UUID | None,
    description: str,
    quantity: int,
    unit_price_cents: int,
    created_by: uuid.UUID,
    order_repo: WorkOrderRepository,
    item_repo: ItemRepository,
    movement_repo: MovementRepository,
) -> tuple[WorkOrder, bool]:
    """Add a quote line, or replay an idempotent add.

    When the order's current status is in ``CONSUMING``, a new inventory
    part line is reconciled (and therefore consumes stock) immediately,
    through the same ``plan_reconciliation`` call every status/line
    change finishes with (``design.md``'s AD-4). A replayed add is a
    no-op and never re-runs reconciliation: the first call already posted
    whatever this line's addition required.

    Raises:
        WorkOrderNotFound: no such order in this workshop.
        WorkOrderLocked: the order's status is ``delivered`` or
            ``cancelled``.
        WorkOrderLineIdConflict: ``line_id`` already exists with
            different fields.
        ItemNotFoundForLine: ``kind == LineKind.inventory_part`` and
            ``item_id`` is missing, foreign, or archived.
    """
    order = order_repo.get_for_update(workshop_id=workshop_id, order_id=order_id)
    if order is None:
        raise WorkOrderNotFound(order_id)

    normalized_description = description.strip()

    existing = _find_line(order, line_id)
    if existing is not None:
        if not _line_fields_match(
            existing,
            kind=kind,
            item_id=item_id,
            description=normalized_description,
            quantity=quantity,
            unit_price_cents=unit_price_cents,
        ):
            raise WorkOrderLineIdConflict(line_id)
        return order, False

    if order.status not in EDITABLE:
        raise WorkOrderLocked(order_id)

    if kind == LineKind.inventory_part:
        item = item_repo.get_by_id(workshop_id=workshop_id, item_id=item_id)
        if item is None or item.archived_at is not None:
            raise ItemNotFoundForLine(item_id)

    now = datetime.now(UTC)
    line = WorkOrderLine(
        id=line_id,
        workshop_id=workshop_id,
        order_id=order_id,
        kind=kind,
        item_id=item_id if kind == LineKind.inventory_part else None,
        description=normalized_description,
        quantity=quantity,
        unit_price_cents=unit_price_cents,
        stock_posted_quantity=0,
        stock_revision=0,
        removed_at=None,
        created_at=now,
        updated_at=now,
    )
    order.lines.append(line)
    order.updated_at = now
    if order.status in CONSUMING:
        # The new line's own row must exist before a posted movement can
        # reference it (`inventory_movements`'s FK to `work_order_lines`),
        # so persist it first; reconciliation below then updates its
        # `stock_posted_quantity`/`stock_revision` in memory, and the
        # final `save` below persists that.
        order_repo.save(order)
        _reconcile_stock(
            order,
            status=order.status,
            now=now,
            created_by=created_by,
            item_repo=item_repo,
            movement_repo=movement_repo,
        )
    order_repo.save(order)
    return order, True


def update_line(
    *,
    workshop_id: uuid.UUID,
    order_id: uuid.UUID,
    line_id: uuid.UUID,
    fields: dict,
    created_by: uuid.UUID,
    order_repo: WorkOrderRepository,
    item_repo: ItemRepository,
    movement_repo: MovementRepository,
) -> WorkOrder:
    """Edit a line's own fields (``description``, ``quantity``,
    ``unit_price_cents``). ``kind`` and ``item_id`` are immutable (the
    ``work-orders`` spec: to change the part, remove the line and add a
    new one).

    When the order's current status is in ``CONSUMING`` and this edit
    changes a part line's quantity, reconciliation posts only the delta
    (``design.md``'s AD-4): a retried edit with the same quantity finds
    ``target == posted`` already and posts nothing.

    Raises:
        WorkOrderNotFound: no such order in this workshop.
        WorkOrderLineNotFound: no such line on this order.
        WorkOrderLocked: the order's status is ``delivered`` or
            ``cancelled``.
    """
    order = order_repo.get_for_update(workshop_id=workshop_id, order_id=order_id)
    if order is None:
        raise WorkOrderNotFound(order_id)

    line = _find_line(order, line_id)
    if line is None or line.removed_at is not None:
        raise WorkOrderLineNotFound(line_id)

    if order.status not in EDITABLE:
        raise WorkOrderLocked(order_id)

    if "description" in fields:
        line.description = fields["description"].strip()
    if "quantity" in fields:
        line.quantity = fields["quantity"]
    if "unit_price_cents" in fields:
        line.unit_price_cents = fields["unit_price_cents"]

    now = datetime.now(UTC)
    line.updated_at = now
    order.updated_at = now
    if order.status in CONSUMING:
        _reconcile_stock(
            order,
            status=order.status,
            now=now,
            created_by=created_by,
            item_repo=item_repo,
            movement_repo=movement_repo,
        )
    order_repo.save(order)
    return order


def remove_line(
    *,
    workshop_id: uuid.UUID,
    order_id: uuid.UUID,
    line_id: uuid.UUID,
    created_by: uuid.UUID,
    order_repo: WorkOrderRepository,
    item_repo: ItemRepository,
    movement_repo: MovementRepository,
) -> WorkOrder:
    """Soft-remove a line, or replay an idempotent remove (removing an
    already-removed line is a no-op: the ``work-orders`` spec's
    "idempotent soft removal").

    When the order's current status is in ``CONSUMING`` and the removed
    line had posted consumption, reconciliation returns it (AD-4: a
    removed line's target drops to 0). An already-removed line returns
    early and never re-runs reconciliation, so a retried remove posts no
    second reversal.

    Raises:
        WorkOrderNotFound: no such order in this workshop.
        WorkOrderLineNotFound: no such line on this order.
        WorkOrderLocked: the order's status is ``delivered`` or
            ``cancelled``.
    """
    order = order_repo.get_for_update(workshop_id=workshop_id, order_id=order_id)
    if order is None:
        raise WorkOrderNotFound(order_id)

    line = _find_line(order, line_id)
    if line is None:
        raise WorkOrderLineNotFound(line_id)

    if line.removed_at is not None:
        return order

    if order.status not in EDITABLE:
        raise WorkOrderLocked(order_id)

    now = datetime.now(UTC)
    line.removed_at = now
    line.updated_at = now
    order.updated_at = now
    if order.status in CONSUMING:
        _reconcile_stock(
            order,
            status=order.status,
            now=now,
            created_by=created_by,
            item_repo=item_repo,
            movement_repo=movement_repo,
        )
    order_repo.save(order)
    return order


def record_payment(
    *,
    workshop_id: uuid.UUID,
    order_id: uuid.UUID,
    payment_id: uuid.UUID,
    amount_cents: int,
    method: PaymentMethod,
    note: str | None,
    created_by: uuid.UUID,
    order_repo: WorkOrderRepository,
    payment_repo: PaymentRepository,
) -> tuple[Payment, bool]:
    """Record a payment against a work order, or replay an idempotent
    create.

    Follows ``design.md``'s AD-11 exact ordering: lock the order row first
    (AD-5's lock order step 1, which also serializes this against a
    concurrent payment or a concurrent cancellation), then the replay
    check (so replaying the exact payment that already settled the order
    is a no-op rather than ``PaymentExceedsBalance`` -- AD-14's ordering
    rule), then the status-in-``PAYABLE`` check, then the balance check,
    then the insert.

    Raises:
        WorkOrderNotFound: no such order in this workshop.
        PaymentIdConflict: ``payment_id`` already exists with different
            fields.
        WorkOrderNotPayable: the order's status is not in ``PAYABLE``.
        PaymentExceedsBalance: ``amount_cents`` is more than the order's
            current balance due (total minus its non-voided payments).
    """
    order = order_repo.get_for_update(workshop_id=workshop_id, order_id=order_id)
    if order is None:
        raise WorkOrderNotFound(order_id)

    normalized_note = _normalize_optional_text(note)

    existing = payment_repo.get_by_id(
        workshop_id=workshop_id, order_id=order_id, payment_id=payment_id
    )
    if existing is not None:
        if not _payment_fields_match(
            existing, amount_cents=amount_cents, method=method, note=normalized_note
        ):
            raise PaymentIdConflict(payment_id)
        return existing, False

    if order.status not in PAYABLE:
        raise WorkOrderNotPayable(order_id)

    payments = payment_repo.list_for_order(workshop_id=workshop_id, order_id=order_id)
    if amount_cents > balance_cents(order.lines, payments):
        raise PaymentExceedsBalance(order_id)

    now = datetime.now(UTC)
    payment = Payment(
        id=payment_id,
        workshop_id=workshop_id,
        order_id=order_id,
        amount_cents=amount_cents,
        method=method,
        note=normalized_note,
        paid_at=now,
        voided_at=None,
        void_reason=None,
        created_by=created_by,
        created_at=now,
    )
    payment_repo.add(payment)
    return payment, True


def void_payment(
    *,
    workshop_id: uuid.UUID,
    order_id: uuid.UUID,
    payment_id: uuid.UUID,
    reason: str,
    order_repo: WorkOrderRepository,
    payment_repo: PaymentRepository,
) -> Payment:
    """Void a recorded payment, or replay an idempotent void.

    Voiding is idempotent (the ``payments`` spec): a second void, with any
    reason, succeeds and returns the payment unchanged, keeping the first
    ``voided_at``. Locks the order row first (``design.md``'s AD-5), even
    though this call never writes the order itself: it serializes against
    a concurrent payment or cancellation reading the same payment list to
    compute a balance or the "has payments" guard.

    Raises:
        WorkOrderNotFound: no such order in this workshop (also covers a
            cross-workshop order id, so tenant isolation never leaks
            whether the order exists).
        PaymentNotFound: no payment ``payment_id`` on this order --
            nonexistent, or recorded against a different order (the spec
            delta from ``tasks.md``'s P3.S1.T1).
    """
    order = order_repo.get_for_update(workshop_id=workshop_id, order_id=order_id)
    if order is None:
        raise WorkOrderNotFound(order_id)

    payment = payment_repo.get_by_id(
        workshop_id=workshop_id, order_id=order_id, payment_id=payment_id
    )
    if payment is None:
        raise PaymentNotFound(payment_id)

    if payment.voided_at is not None:
        return payment

    payment.voided_at = datetime.now(UTC)
    payment.void_reason = reason
    payment_repo.save(payment)
    return payment


def daily_cash_summary(
    *,
    workshop_id: uuid.UUID,
    day: date | None,
    clock: Clock,
    payment_repo: PaymentRepository,
    order_repo: WorkOrderRepository,
) -> tuple[date, dict[PaymentMethod, int], list[CashSummaryEntry]]:
    """The workshop's recorded payments for one `America/Tegucigalpa`
    calendar day, broken down by payment method (``design.md``'s AD-20).

    ``day`` defaults to "today" in that time zone. The range queried is
    the sargable ``[start, end)`` AD-20 specifies, so it uses the
    ``(workshop_id, paid_at)`` index instead of a per-row timezone
    conversion. Every voided payment is excluded, both from the totals
    and from the listed payments, as though it had never been recorded.

    Returns the resolved day (useful when ``day`` was defaulted), the
    per-method totals in cents (all four `PaymentMethod` keys always
    present, 0 when a method had no payments that day), and the day's
    non-voided payments paired with their order number.
    """
    resolved_day = day if day is not None else clock.now().astimezone(HONDURAS_TZ).date()
    start = datetime.combine(resolved_day, time.min, HONDURAS_TZ)
    end = datetime.combine(resolved_day + timedelta(days=1), time.min, HONDURAS_TZ)

    payments = [
        payment
        for payment in payment_repo.list_for_workshop_day(
            workshop_id=workshop_id, start=start, end=end
        )
        if payment.voided_at is None
    ]

    totals_cents: dict[PaymentMethod, int] = dict.fromkeys(PaymentMethod, 0)
    for payment in payments:
        totals_cents[payment.method] += payment.amount_cents

    order_numbers = order_repo.numbers(
        workshop_id=workshop_id, order_ids=[payment.order_id for payment in payments]
    )
    entries = [
        CashSummaryEntry(payment=payment, order_number=order_numbers[payment.order_id])
        for payment in payments
    ]
    return resolved_day, totals_cents, entries

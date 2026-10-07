"""Use cases for the work-orders feature: orders, numbering, and quote
lines in non-consuming statuses.

Stock reconciliation (status changes, and line edits/removal while a line
is already consuming) is wired in Slice 3's ``change_status``; this slice
only ever leaves lines at ``stock_posted_quantity == 0`` because every
order it creates stays in ``quote``, the only status reachable without the
Slice-3 status endpoint.
"""

import uuid
from datetime import UTC, datetime
from typing import Literal

from taller.customers.application.ports import VehicleRepository
from taller.customers.application.use_cases import get_active_vehicle
from taller.inventory.application.ports import ItemRepository
from taller.workorders.application.ports import WorkOrderRepository, WorkshopCounterRepository
from taller.workorders.domain.entities import LineKind, WorkOrder, WorkOrderLine
from taller.workorders.domain.errors import (
    ItemNotFoundForLine,
    WorkOrderIdConflict,
    WorkOrderLineIdConflict,
    WorkOrderLineNotFound,
    WorkOrderLocked,
    WorkOrderNotFound,
)
from taller.workorders.domain.status import EDITABLE, WorkOrderStatus

#: The named counter `create_work_order` bumps for every new order
#: (`design.md`'s AD-6). One counter per workshop, keyed by this name.
ORDER_COUNTER_NAME = "work_order"

#: `GET /work-orders`'s `limit` query parameter is capped at this value
#: regardless of what the caller asks for.
MAX_LIST_LIMIT = 100

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

    Raises:
        WorkOrderNotFound: no such order in this workshop.
        WorkOrderLocked: the order's status is ``delivered`` or
            ``cancelled``.
    """
    order = order_repo.get_by_id(workshop_id=workshop_id, order_id=order_id)
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
    order_repo: WorkOrderRepository,
    item_repo: ItemRepository,
) -> tuple[WorkOrder, bool]:
    """Add a quote line, or replay an idempotent add.

    This slice never posts a movement from adding a line: every order it
    can reach is still in ``quote`` (the only status creatable without
    Slice 3's status endpoint), which is outside ``CONSUMING``. Posting
    for a line added while already consuming arrives with Slice 3's
    ``change_status``, through the same ``plan_reconciliation`` call every
    status/line change finishes with.

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
    order_repo.save(order)
    return order, True


def update_line(
    *,
    workshop_id: uuid.UUID,
    order_id: uuid.UUID,
    line_id: uuid.UUID,
    fields: dict,
    order_repo: WorkOrderRepository,
) -> WorkOrder:
    """Edit a line's own fields (``description``, ``quantity``,
    ``unit_price_cents``). ``kind`` and ``item_id`` are immutable (the
    ``work-orders`` spec: to change the part, remove the line and add a
    new one).

    This slice posts no movement for a quantity edit: stock reconciliation
    while consuming arrives with Slice 3.

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
    order_repo.save(order)
    return order


def remove_line(
    *,
    workshop_id: uuid.UUID,
    order_id: uuid.UUID,
    line_id: uuid.UUID,
    order_repo: WorkOrderRepository,
) -> WorkOrder:
    """Soft-remove a line, or replay an idempotent remove (removing an
    already-removed line is a no-op: the ``work-orders`` spec's
    "idempotent soft removal").

    This slice posts no reversal movement: a removed line that had
    already consumed stock is reconciled by Slice 3's
    ``change_status``/line-edit wiring, which both finish with the same
    ``plan_reconciliation`` call.

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
    order_repo.save(order)
    return order

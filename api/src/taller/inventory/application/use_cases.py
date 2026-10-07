"""Use cases for the inventory feature: items and their stock movement ledger."""

import uuid
from datetime import UTC, datetime

from taller.inventory.application.ports import ItemRepository, MovementRepository
from taller.inventory.domain.entities import Item, StockMovement
from taller.inventory.domain.errors import (
    ItemIdConflict,
    ItemNameTaken,
    ItemNotFound,
    MovementIdConflict,
    StockOutOfRange,
)
from taller.inventory.domain.item_name import normalize_item_name
from taller.inventory.domain.stock import compute_delta, is_stock_in_range

#: Note recorded on the implicit adjustment created by `initial_stock`.
INITIAL_STOCK_NOTE = "Inventario inicial"

#: Fixed namespace for deriving a deterministic initial-stock movement id
#: from an item id (see `_initial_movement_id`). `uuid5` is a pure function
#: of its inputs, so this is identical across every process and run.
_INITIAL_STOCK_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_URL, "https://taller-mecanico.invalid/inventory/initial-stock"
)


def _initial_movement_id(item_id: uuid.UUID) -> uuid.UUID:
    """Deterministic id for an item's implicit initial-stock movement.

    Lets a replayed ``POST /items`` load the movement it created the first
    time (see `_initial_stock_matches`) instead of being unable to see it,
    the way a random id would.
    """
    return uuid.uuid5(_INITIAL_STOCK_NAMESPACE, str(item_id))


def _initial_stock_matches(
    *,
    workshop_id: uuid.UUID,
    item_id: uuid.UUID,
    initial_stock: int | None,
    movement_repo: MovementRepository,
) -> bool:
    """Whether a replayed create's `initial_stock` matches what was recorded.

    Compares both presence (was an initial movement recorded at all) and
    quantity, since `initial_stock=None` (no movement) and `initial_stock=0`
    (a recorded zero-quantity adjustment) are different, observable states.
    The movement must also be exactly what `create_item` records (an
    `adjust` with the initial-stock note, for this item): the id is
    derivable, so a client could have recorded some other movement there
    first, and that is not this item's initial stock.
    """
    existing_movement = movement_repo.get_by_id(
        workshop_id=workshop_id, movement_id=_initial_movement_id(item_id)
    )
    if initial_stock is None:
        return existing_movement is None
    return existing_movement is not None and _movement_matches(
        existing_movement,
        item_id=item_id,
        kind="adjust",
        quantity=initial_stock,
        note=INITIAL_STOCK_NOTE,
    )


def _normalize_unit(raw: str | None) -> str:
    cleaned = (raw or "").strip()
    return cleaned or "unidad"


def _normalize_optional_text(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip()
    return cleaned or None


def _item_fields_match(
    item: Item,
    *,
    name: str,
    category: str | None,
    unit: str,
    min_stock: int,
    sale_price_cents: int | None,
    notes: str | None,
) -> bool:
    return (
        item.name == name
        and item.category == category
        and item.unit == unit
        and item.min_stock == min_stock
        and item.sale_price_cents == sale_price_cents
        and item.notes == notes
    )


def create_item(
    *,
    workshop_id: uuid.UUID,
    item_id: uuid.UUID | None,
    name: str,
    category: str | None,
    unit: str | None,
    min_stock: int,
    sale_price_cents: int | None,
    notes: str | None,
    initial_stock: int | None,
    created_by: uuid.UUID,
    item_repo: ItemRepository,
    movement_repo: MovementRepository,
) -> tuple[Item, bool]:
    """Create an item, or replay an idempotent create.

    Returns ``(item, is_new)``: ``is_new`` is False when ``item_id`` already
    existed with identical fields *and* the same ``initial_stock`` (the
    caller should respond 200, not 201).

    Raises:
        ItemIdConflict: ``item_id`` already exists with different fields,
            or with the same fields but a different ``initial_stock`` than
            what was originally recorded.
        ItemNameTaken: another active item already has this name.
    """
    normalized_name = normalize_item_name(name)
    normalized_category = _normalize_optional_text(category)
    normalized_unit = _normalize_unit(unit)
    normalized_notes = _normalize_optional_text(notes)

    if item_id is not None:
        existing = item_repo.get_by_id(workshop_id=workshop_id, item_id=item_id)
        if existing is not None:
            if not _item_fields_match(
                existing,
                name=normalized_name,
                category=normalized_category,
                unit=normalized_unit,
                min_stock=min_stock,
                sale_price_cents=sale_price_cents,
                notes=normalized_notes,
            ):
                raise ItemIdConflict(item_id)
            if not _initial_stock_matches(
                workshop_id=workshop_id,
                item_id=item_id,
                initial_stock=initial_stock,
                movement_repo=movement_repo,
            ):
                raise ItemIdConflict(item_id)
            return existing, False

    if item_repo.get_active_by_name(workshop_id=workshop_id, name=normalized_name) is not None:
        raise ItemNameTaken(normalized_name)

    now = datetime.now(UTC)
    item = Item(
        id=item_id if item_id is not None else uuid.uuid4(),
        workshop_id=workshop_id,
        name=normalized_name,
        category=normalized_category,
        unit=normalized_unit,
        min_stock=min_stock,
        sale_price_cents=sale_price_cents,
        notes=normalized_notes,
        stock=0,
        archived_at=None,
        created_at=now,
        updated_at=now,
    )
    item_repo.add(item)

    if initial_stock is not None:
        delta = compute_delta(kind="adjust", quantity=initial_stock, current_stock=0)
        movement = StockMovement(
            id=_initial_movement_id(item.id),
            workshop_id=workshop_id,
            item_id=item.id,
            kind="adjust",
            quantity=initial_stock,
            delta=delta,
            note=INITIAL_STOCK_NOTE,
            occurred_at=now,
            recorded_at=now,
            created_by=created_by,
        )
        movement_repo.add(movement)
        item.stock = delta
        item.updated_at = now
        item_repo.save(item)

    return item, True


def get_item(*, workshop_id: uuid.UUID, item_id: uuid.UUID, item_repo: ItemRepository) -> Item:
    """Raises: ItemNotFound: no such item in this workshop."""
    item = item_repo.get_by_id(workshop_id=workshop_id, item_id=item_id)
    if item is None:
        raise ItemNotFound(item_id)
    return item


def list_items(
    *,
    workshop_id: uuid.UUID,
    query: str | None,
    low_stock_only: bool,
    include_archived: bool,
    item_repo: ItemRepository,
) -> list[Item]:
    cleaned_query = query.strip() if query else None
    return item_repo.list(
        workshop_id=workshop_id,
        query=cleaned_query or None,
        low_stock_only=low_stock_only,
        include_archived=include_archived,
    )


def update_item(
    *,
    workshop_id: uuid.UUID,
    item_id: uuid.UUID,
    fields: dict,
    item_repo: ItemRepository,
) -> Item:
    """Update any item field present in ``fields``, except stock.

    ``fields`` only contains keys the caller explicitly set (e.g. via
    Pydantic's ``exclude_unset``), so omitted fields are left untouched and
    an explicit null clears an optional field.

    Raises:
        ItemNotFound: no such item in this workshop.
        ItemNameTaken: the new name collides with another active item.
    """
    item = item_repo.get_by_id(workshop_id=workshop_id, item_id=item_id)
    if item is None:
        raise ItemNotFound(item_id)

    if "name" in fields:
        new_name = normalize_item_name(fields["name"])
        if new_name != item.name:
            collision = item_repo.get_active_by_name(
                workshop_id=workshop_id, name=new_name, exclude_id=item.id
            )
            if collision is not None:
                raise ItemNameTaken(new_name)
        item.name = new_name
    if "category" in fields:
        item.category = _normalize_optional_text(fields["category"])
    if "unit" in fields:
        item.unit = _normalize_unit(fields["unit"])
    if "min_stock" in fields:
        item.min_stock = fields["min_stock"]
    if "sale_price_cents" in fields:
        item.sale_price_cents = fields["sale_price_cents"]
    if "notes" in fields:
        item.notes = _normalize_optional_text(fields["notes"])

    item.updated_at = datetime.now(UTC)
    item_repo.save(item)
    return item


def archive_item(*, workshop_id: uuid.UUID, item_id: uuid.UUID, item_repo: ItemRepository) -> None:
    """Raises: ItemNotFound: no such item in this workshop."""
    item = item_repo.get_by_id(workshop_id=workshop_id, item_id=item_id)
    if item is None:
        raise ItemNotFound(item_id)
    if item.archived_at is None:
        now = datetime.now(UTC)
        item.archived_at = now
        item.updated_at = now
        item_repo.save(item)


def list_item_movements(
    *,
    workshop_id: uuid.UUID,
    item_id: uuid.UUID,
    limit: int,
    item_repo: ItemRepository,
    movement_repo: MovementRepository,
) -> list[StockMovement]:
    """Raises: ItemNotFound: no such item in this workshop."""
    if item_repo.get_by_id(workshop_id=workshop_id, item_id=item_id) is None:
        raise ItemNotFound(item_id)
    capped_limit = min(limit, 200)
    return movement_repo.list_for_item(workshop_id=workshop_id, item_id=item_id, limit=capped_limit)


def _movement_matches(
    existing: StockMovement, *, item_id: uuid.UUID, kind: str, quantity: int, note: str | None
) -> bool:
    return (
        existing.item_id == item_id
        and existing.kind == kind
        and existing.quantity == quantity
        and existing.note == note
    )


def record_movement(
    *,
    workshop_id: uuid.UUID,
    movement_id: uuid.UUID,
    item_id: uuid.UUID,
    kind: str,
    quantity: int,
    note: str | None,
    occurred_at: datetime | None,
    created_by: uuid.UUID,
    item_repo: ItemRepository,
    movement_repo: MovementRepository,
) -> tuple[StockMovement, Item, bool]:
    """Record a stock movement, or replay an idempotent one.

    Returns ``(movement, item, is_new)``: ``is_new`` is False when
    ``movement_id`` already existed with the same ``item_id``/``kind``/
    ``quantity``/``note`` (the caller should respond 200, not 201); nothing
    is changed in that case.

    Raises:
        ItemNotFound: no such item in this workshop (archived items still
            accept movements, so an offline replay always applies).
        MovementIdConflict: ``movement_id`` already exists with a different
            payload.
        StockOutOfRange: applying this movement would push the item's
            cached stock outside PostgreSQL's `integer` column range.
    """
    existing = movement_repo.get_by_id(workshop_id=workshop_id, movement_id=movement_id)
    if existing is not None:
        if _movement_matches(existing, item_id=item_id, kind=kind, quantity=quantity, note=note):
            item = item_repo.get_by_id(workshop_id=workshop_id, item_id=existing.item_id)
            if item is None:
                raise ItemNotFound(item_id)
            return existing, item, False
        raise MovementIdConflict(movement_id)

    item = item_repo.get_for_update(workshop_id=workshop_id, item_id=item_id)
    if item is None:
        raise ItemNotFound(item_id)

    delta = compute_delta(kind=kind, quantity=quantity, current_stock=item.stock)
    new_stock = item.stock + delta
    if not is_stock_in_range(new_stock):
        raise StockOutOfRange(item_id=item_id, resulting_stock=new_stock)

    now = datetime.now(UTC)
    movement = StockMovement(
        id=movement_id,
        workshop_id=workshop_id,
        item_id=item_id,
        kind=kind,
        quantity=quantity,
        delta=delta,
        note=note,
        occurred_at=occurred_at or now,
        recorded_at=now,
        created_by=created_by,
    )
    movement_repo.add(movement)

    item.stock = new_stock
    item.updated_at = now
    item_repo.save(item)

    return movement, item, True

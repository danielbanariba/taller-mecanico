"""SQLAlchemy-backed adapters for the inventory ports."""

import uuid

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from taller.inventory.adapters.models import ItemModel, StockMovementModel
from taller.inventory.domain.entities import Item, StockMovement


def _item_from_model(model: ItemModel) -> Item:
    return Item(
        id=model.id,
        workshop_id=model.workshop_id,
        name=model.name,
        category=model.category,
        unit=model.unit,
        min_stock=model.min_stock,
        sale_price_cents=model.sale_price_cents,
        notes=model.notes,
        stock=model.stock,
        archived_at=model.archived_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


#: Character used to escape `%`/`_` when building a `LIKE` pattern from a
#: user-supplied search term, passed explicitly via `.like(..., escape=...)`
#: rather than relying on any database's default.
_LIKE_ESCAPE_CHAR = "\\"


def _escape_like(raw: str) -> str:
    """Escape `LIKE` metacharacters so `raw` matches only literally.

    Without this, a search term containing `%` or `_` (e.g. a part number
    like "M8_10", or "50% descuento") would trigger unintended SQL wildcard
    matching instead of a literal substring search. The escape character
    itself must be escaped first, so a literal backslash in the term is
    never mistaken for the start of an escape sequence.
    """
    escaped = raw.replace(_LIKE_ESCAPE_CHAR, _LIKE_ESCAPE_CHAR * 2)
    escaped = escaped.replace("%", f"{_LIKE_ESCAPE_CHAR}%")
    return escaped.replace("_", f"{_LIKE_ESCAPE_CHAR}_")


def _movement_from_model(model: StockMovementModel) -> StockMovement:
    return StockMovement(
        id=model.id,
        workshop_id=model.workshop_id,
        item_id=model.item_id,
        kind=model.kind,
        quantity=model.quantity,
        delta=model.delta,
        note=model.note,
        occurred_at=model.occurred_at,
        recorded_at=model.recorded_at,
        created_by=model.created_by,
    )


class SqlAlchemyItemRepository:
    """Item persistence backed by SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, *, workshop_id: uuid.UUID, item_id: uuid.UUID) -> Item | None:
        model = (
            self._session.query(ItemModel)
            .filter(ItemModel.id == item_id, ItemModel.workshop_id == workshop_id)
            .one_or_none()
        )
        return _item_from_model(model) if model is not None else None

    def get_for_update(self, *, workshop_id: uuid.UUID, item_id: uuid.UUID) -> Item | None:
        model = (
            self._session.query(ItemModel)
            .filter(ItemModel.id == item_id, ItemModel.workshop_id == workshop_id)
            .with_for_update()
            .one_or_none()
        )
        return _item_from_model(model) if model is not None else None

    def get_active_by_name(
        self, *, workshop_id: uuid.UUID, name: str, exclude_id: uuid.UUID | None = None
    ) -> Item | None:
        # `taller_unaccent_lower` is the same IMMUTABLE wrapper the migration
        # uses for the partial unique index, so this check and the database
        # guarantee agree on what counts as a duplicate name (see the
        # migration for why a plain `unaccent(lower(...))` cannot be used).
        normalized_target = func.taller_unaccent_lower(name)
        query = self._session.query(ItemModel).filter(
            ItemModel.workshop_id == workshop_id,
            ItemModel.archived_at.is_(None),
            func.taller_unaccent_lower(ItemModel.name) == normalized_target,
        )
        if exclude_id is not None:
            query = query.filter(ItemModel.id != exclude_id)
        model = query.one_or_none()
        return _item_from_model(model) if model is not None else None

    def add(self, item: Item) -> None:
        self._session.add(
            ItemModel(
                id=item.id,
                workshop_id=item.workshop_id,
                name=item.name,
                category=item.category,
                unit=item.unit,
                min_stock=item.min_stock,
                sale_price_cents=item.sale_price_cents,
                notes=item.notes,
                stock=item.stock,
                archived_at=item.archived_at,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )
        self._session.flush()

    def save(self, item: Item) -> None:
        model = self._session.get(ItemModel, item.id)
        if model is None:
            return
        model.name = item.name
        model.category = item.category
        model.unit = item.unit
        model.min_stock = item.min_stock
        model.sale_price_cents = item.sale_price_cents
        model.notes = item.notes
        model.stock = item.stock
        model.archived_at = item.archived_at
        model.updated_at = item.updated_at
        self._session.flush()

    def list(
        self,
        *,
        workshop_id: uuid.UUID,
        query: str | None,
        low_stock_only: bool,
        include_archived: bool,
    ) -> list[Item]:
        q = self._session.query(ItemModel).filter(ItemModel.workshop_id == workshop_id)
        if not include_archived:
            q = q.filter(ItemModel.archived_at.is_(None))
        if query:
            pattern = func.taller_unaccent_lower(f"%{_escape_like(query)}%")
            q = q.filter(
                or_(
                    func.taller_unaccent_lower(ItemModel.name).like(
                        pattern, escape=_LIKE_ESCAPE_CHAR
                    ),
                    and_(
                        ItemModel.category.is_not(None),
                        func.taller_unaccent_lower(ItemModel.category).like(
                            pattern, escape=_LIKE_ESCAPE_CHAR
                        ),
                    ),
                )
            )
        if low_stock_only:
            q = q.filter(ItemModel.min_stock > 0, ItemModel.stock <= ItemModel.min_stock)
        q = q.order_by(ItemModel.name.asc())
        return [_item_from_model(model) for model in q.all()]


class SqlAlchemyMovementRepository:
    """Stock movement ledger persistence backed by SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, *, workshop_id: uuid.UUID, movement_id: uuid.UUID) -> StockMovement | None:
        model = (
            self._session.query(StockMovementModel)
            .filter(
                StockMovementModel.id == movement_id,
                StockMovementModel.workshop_id == workshop_id,
            )
            .one_or_none()
        )
        return _movement_from_model(model) if model is not None else None

    def add(self, movement: StockMovement) -> None:
        self._session.add(
            StockMovementModel(
                id=movement.id,
                workshop_id=movement.workshop_id,
                item_id=movement.item_id,
                kind=movement.kind,
                quantity=movement.quantity,
                delta=movement.delta,
                note=movement.note,
                occurred_at=movement.occurred_at,
                recorded_at=movement.recorded_at,
                created_by=movement.created_by,
            )
        )
        self._session.flush()

    def list_for_item(
        self, *, workshop_id: uuid.UUID, item_id: uuid.UUID, limit: int
    ) -> list[StockMovement]:
        models = (
            self._session.query(StockMovementModel)
            .filter(
                StockMovementModel.workshop_id == workshop_id,
                StockMovementModel.item_id == item_id,
            )
            .order_by(StockMovementModel.recorded_at.desc())
            .limit(limit)
            .all()
        )
        return [_movement_from_model(model) for model in models]

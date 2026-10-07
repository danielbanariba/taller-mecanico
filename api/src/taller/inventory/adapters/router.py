"""HTTP routes for inventory items and their stock movement ledger."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from taller.identity.adapters.dependencies import get_current_user, get_current_workshop_id
from taller.identity.domain.entities import User
from taller.inventory.adapters.repositories import (
    SqlAlchemyItemRepository,
    SqlAlchemyMovementRepository,
)
from taller.inventory.adapters.schemas import (
    ItemCreateRequest,
    ItemOut,
    ItemUpdateRequest,
    MovementCreateRequest,
    MovementItemSummary,
    MovementOut,
    MovementRecordResponse,
)
from taller.inventory.application.use_cases import (
    archive_item,
    create_item,
    get_item,
    list_item_movements,
    list_items,
    record_movement,
    update_item,
)
from taller.inventory.domain.entities import Item
from taller.inventory.domain.errors import (
    ItemIdConflict,
    ItemNameTaken,
    ItemNotFound,
    MovementIdConflict,
    StockOutOfRange,
)
from taller.shared.db import get_db

router = APIRouter(prefix="/inventory", tags=["inventory"])

#: Default PostgreSQL primary key constraint names (no explicit name was
#: given in the migration, so these are the `<table>_pkey` defaults). Item
#: and movement ids are global primary keys, not scoped to a workshop, so a
#: client-supplied id colliding with another workshop's row surfaces here
#: as a violation of one of these constraints, never as the workshop-scoped
#: pre-check (which cannot see the other workshop's row at all).
_ITEM_PK_CONSTRAINT = "inventory_items_pkey"
_MOVEMENT_PK_CONSTRAINT = "inventory_movements_pkey"

#: The partial unique index on active item names (created in the inventory
#: migration with raw SQL, hence no SQLAlchemy-generated name to import).
_ACTIVE_NAME_INDEX = "ix_inventory_items_active_name"


def _violated_constraint(exc: IntegrityError) -> str | None:
    """Mirrors `taller.identity.adapters.router._violated_constraint`."""
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


def _item_conflict(exc: Exception) -> HTTPException:
    if isinstance(exc, ItemIdConflict):
        return HTTPException(status.HTTP_409_CONFLICT, detail="item_id_conflict")
    return HTTPException(status.HTTP_409_CONFLICT, detail="item_name_taken")


@router.get("/items", response_model=list[ItemOut])
def list_items_route(
    q: str | None = Query(default=None),
    low_stock: bool = Query(default=False),
    include_archived: bool = Query(default=False),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> list[ItemOut]:
    item_repo = SqlAlchemyItemRepository(db)
    items = list_items(
        workshop_id=workshop_id,
        query=q,
        low_stock_only=low_stock,
        include_archived=include_archived,
        item_repo=item_repo,
    )
    return [ItemOut.from_domain(item) for item in items]


@router.post("/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item_route(
    payload: ItemCreateRequest,
    response: Response,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItemOut:
    item_repo = SqlAlchemyItemRepository(db)
    movement_repo = SqlAlchemyMovementRepository(db)

    def _attempt() -> tuple[Item, bool]:
        result = create_item(
            workshop_id=workshop_id,
            item_id=payload.id,
            name=payload.name,
            category=payload.category,
            unit=payload.unit,
            min_stock=payload.min_stock,
            sale_price_cents=payload.sale_price_cents,
            notes=payload.notes,
            initial_stock=payload.initial_stock,
            created_by=current_user.id,
            item_repo=item_repo,
            movement_repo=movement_repo,
        )
        db.commit()
        return result

    try:
        item, is_new = _attempt()
    except (ItemIdConflict, ItemNameTaken) as exc:
        db.rollback()
        raise _item_conflict(exc) from exc
    except IntegrityError as first_exc:
        db.rollback()
        # Another request committed a colliding id/name between our
        # pre-check and our insert. Retry once: the pre-check now sees the
        # committed row and raises the precise conflict instead of a raw
        # database error.
        try:
            item, is_new = _attempt()
        except (ItemIdConflict, ItemNameTaken) as exc:
            db.rollback()
            raise _item_conflict(exc) from exc
        except IntegrityError as exc:
            db.rollback()
            # A client-supplied id already used by another workshop: our
            # tenant-scoped pre-check cannot see that row even on retry, so
            # it never resolves into ItemIdConflict above. Report the same
            # 409 a same-workshop id conflict gets, and nothing else about
            # the other workshop's row. Any other integrity error here is a
            # genuine bug and must not be reported as a conflict.
            if _violated_constraint(exc) == _ITEM_PK_CONSTRAINT:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="item_id_conflict") from exc
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail="item_create_failed"
            ) from (exc or first_exc)

    if not is_new:
        response.status_code = status.HTTP_200_OK
    return ItemOut.from_domain(item)


@router.get("/items/{item_id}", response_model=ItemOut)
def get_item_route(
    item_id: uuid.UUID,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> ItemOut:
    item_repo = SqlAlchemyItemRepository(db)
    try:
        item = get_item(workshop_id=workshop_id, item_id=item_id, item_repo=item_repo)
    except ItemNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="item_not_found") from exc
    return ItemOut.from_domain(item)


@router.patch("/items/{item_id}", response_model=ItemOut)
def update_item_route(
    item_id: uuid.UUID,
    payload: ItemUpdateRequest,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> ItemOut:
    item_repo = SqlAlchemyItemRepository(db)
    fields = payload.model_dump(exclude_unset=True)
    try:
        item = update_item(
            workshop_id=workshop_id, item_id=item_id, fields=fields, item_repo=item_repo
        )
        db.commit()
    except ItemNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="item_not_found") from exc
    except ItemNameTaken as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="item_name_taken") from exc
    except IntegrityError as exc:
        db.rollback()
        # A concurrent rename committed the same name after our pre-check:
        # the unique index is the real guarantee. Any other integrity error
        # is a bug and must not be reported as a taken name.
        if _violated_constraint(exc) != _ACTIVE_NAME_INDEX:
            raise
        raise HTTPException(status.HTTP_409_CONFLICT, detail="item_name_taken") from exc
    return ItemOut.from_domain(item)


@router.post("/items/{item_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_item_route(
    item_id: uuid.UUID,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> None:
    item_repo = SqlAlchemyItemRepository(db)
    try:
        archive_item(workshop_id=workshop_id, item_id=item_id, item_repo=item_repo)
        db.commit()
    except ItemNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="item_not_found") from exc


@router.get("/items/{item_id}/movements", response_model=list[MovementOut])
def list_item_movements_route(
    item_id: uuid.UUID,
    limit: int = Query(default=50, ge=1),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> list[MovementOut]:
    item_repo = SqlAlchemyItemRepository(db)
    movement_repo = SqlAlchemyMovementRepository(db)
    try:
        movements = list_item_movements(
            workshop_id=workshop_id,
            item_id=item_id,
            limit=limit,
            item_repo=item_repo,
            movement_repo=movement_repo,
        )
    except ItemNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="item_not_found") from exc
    return [MovementOut.from_domain(movement) for movement in movements]


@router.put("/movements/{movement_id}", response_model=MovementRecordResponse)
def record_movement_route(
    movement_id: uuid.UUID,
    payload: MovementCreateRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MovementRecordResponse:
    item_repo = SqlAlchemyItemRepository(db)
    movement_repo = SqlAlchemyMovementRepository(db)
    workshop_id = current_user.workshop_id

    def _attempt() -> tuple:
        result = record_movement(
            workshop_id=workshop_id,
            movement_id=movement_id,
            item_id=payload.item_id,
            kind=payload.kind,
            quantity=payload.quantity,
            note=payload.note,
            occurred_at=payload.occurred_at,
            created_by=current_user.id,
            item_repo=item_repo,
            movement_repo=movement_repo,
        )
        db.commit()
        return result

    try:
        movement, item, is_new = _attempt()
    except ItemNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="item_not_found") from exc
    except MovementIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="movement_id_conflict") from exc
    except StockOutOfRange as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="stock_out_of_range"
        ) from exc
    except IntegrityError as first_exc:
        db.rollback()
        # Another request committed the same movement id between our
        # pre-check and our insert; retry once so the pre-check resolves it
        # as a replay or a precise conflict.
        try:
            movement, item, is_new = _attempt()
        except ItemNotFound as exc:
            db.rollback()
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="item_not_found") from exc
        except MovementIdConflict as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, detail="movement_id_conflict") from exc
        except StockOutOfRange as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail="stock_out_of_range"
            ) from exc
        except IntegrityError as exc:
            db.rollback()
            # A client-supplied movement id already used by another
            # workshop: our tenant-scoped pre-check cannot see that row
            # even on retry. Report the same 409 a same-workshop id
            # conflict gets. Any other integrity error here is a genuine
            # bug and must not be reported as a conflict.
            if _violated_constraint(exc) == _MOVEMENT_PK_CONSTRAINT:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, detail="movement_id_conflict"
                ) from exc
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail="movement_record_failed"
            ) from (exc or first_exc)

    response.status_code = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
    return MovementRecordResponse(
        movement=MovementOut.from_domain(movement), item=MovementItemSummary.from_domain(item)
    )

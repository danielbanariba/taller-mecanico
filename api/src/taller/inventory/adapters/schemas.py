"""Pydantic request/response schemas for the inventory HTTP API."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from taller.inventory.domain.entities import Item, StockMovement
from taller.inventory.domain.errors import InvalidItemName, InvalidMovementQuantity
from taller.inventory.domain.item_name import normalize_item_name
from taller.inventory.domain.stock import MAX_QUANTITY, validate_quantity

#: Keeps `sale_price_cents` (HNL, integer cents) within a sane range. The
#: domain entity has no price validation of its own (unlike quantities,
#: which share `MAX_QUANTITY` through `taller.inventory.domain.stock`), so
#: this 422 is the only guard against an overflowing value.
MAX_SALE_PRICE_CENTS = 1_000_000_000


def _validate_name(value: str) -> str:
    """Normalize a name field, surfacing the domain error as a Pydantic one.

    Mirrors ``taller.identity.adapters.schemas._validate_phone``: raising
    ``ValueError`` here lets FastAPI turn an invalid name into a 422
    response automatically.
    """
    try:
        return normalize_item_name(value)
    except InvalidItemName as exc:
        raise ValueError(str(exc)) from exc


class ItemCreateRequest(BaseModel):
    id: uuid.UUID | None = None
    name: str
    category: str | None = None
    unit: str = "unidad"
    min_stock: int = Field(default=0, ge=0, le=MAX_QUANTITY)
    sale_price_cents: int | None = Field(default=None, ge=0, le=MAX_SALE_PRICE_CENTS)
    notes: str | None = None
    initial_stock: int | None = Field(default=None, ge=0, le=MAX_QUANTITY)

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, value: str) -> str:
        return _validate_name(value)


class ItemUpdateRequest(BaseModel):
    """All fields except stock; only explicitly set fields are applied."""

    name: str | None = None
    category: str | None = None
    unit: str | None = None
    min_stock: int | None = Field(default=None, ge=0, le=MAX_QUANTITY)
    sale_price_cents: int | None = Field(default=None, ge=0, le=MAX_SALE_PRICE_CENTS)
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, value: str | None) -> str | None:
        return _validate_name(value) if value is not None else value


class ItemOut(BaseModel):
    id: uuid.UUID
    name: str
    category: str | None
    unit: str
    min_stock: int
    sale_price_cents: int | None
    notes: str | None
    stock: int
    needs_review: bool
    is_low: bool
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, item: Item) -> "ItemOut":
        return cls(
            id=item.id,
            name=item.name,
            category=item.category,
            unit=item.unit,
            min_stock=item.min_stock,
            sale_price_cents=item.sale_price_cents,
            notes=item.notes,
            stock=item.stock,
            needs_review=item.needs_review,
            is_low=item.is_low,
            archived_at=item.archived_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )


class MovementCreateRequest(BaseModel):
    item_id: uuid.UUID
    kind: Literal["in", "out", "adjust"]
    quantity: int = Field(ge=0, le=MAX_QUANTITY)
    note: str | None = None
    occurred_at: datetime | None = None

    @model_validator(mode="after")
    def _validate_quantity_for_kind(self) -> "MovementCreateRequest":
        try:
            validate_quantity(kind=self.kind, quantity=self.quantity)
        except InvalidMovementQuantity as exc:
            raise ValueError(str(exc)) from exc
        return self


class MovementOut(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    kind: str
    quantity: int
    delta: int
    note: str | None
    occurred_at: datetime
    recorded_at: datetime
    created_by: uuid.UUID

    @classmethod
    def from_domain(cls, movement: StockMovement) -> "MovementOut":
        return cls(
            id=movement.id,
            item_id=movement.item_id,
            kind=movement.kind,
            quantity=movement.quantity,
            delta=movement.delta,
            note=movement.note,
            occurred_at=movement.occurred_at,
            recorded_at=movement.recorded_at,
            created_by=movement.created_by,
        )


class MovementItemSummary(BaseModel):
    """Just enough of the item for the client to update its UI after
    recording a movement, without a full item re-fetch.
    """

    id: uuid.UUID
    stock: int
    needs_review: bool
    is_low: bool

    @classmethod
    def from_domain(cls, item: Item) -> "MovementItemSummary":
        return cls(id=item.id, stock=item.stock, needs_review=item.needs_review, is_low=item.is_low)


class MovementRecordResponse(BaseModel):
    movement: MovementOut
    item: MovementItemSummary

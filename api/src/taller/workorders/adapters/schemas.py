"""Pydantic request/response schemas for the work-orders HTTP API."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from taller.customers.domain.entities import Customer, Vehicle, VehicleType
from taller.workorders.domain.entities import LineKind, WorkOrder, WorkOrderLine
from taller.workorders.domain.money import line_subtotal_cents, order_total_cents
from taller.workorders.domain.status import EDITABLE, TRANSITIONS, WorkOrderStatus

#: Design's bound for `odometer_km`.
MAX_ODOMETER_KM = 2_000_000


class WorkOrderCreateRequest(BaseModel):
    """`id` is required, unlike items/customers/vehicles: an order create
    without a client id cannot be made retry-safe, and a retry would burn
    a number (`design.md`'s AD-14).
    """

    id: uuid.UUID
    vehicle_id: uuid.UUID
    complaint: str | None = Field(default=None, max_length=1000)
    odometer_km: int | None = Field(default=None, ge=0, le=MAX_ODOMETER_KM)
    notes: str | None = None


class WorkOrderUpdateRequest(BaseModel):
    """Only explicitly set fields are applied. Every field is nullable at
    the domain level, so an explicit `null` is a valid way to clear it --
    unlike `CustomerUpdateRequest.full_name`, none of these need a
    reject-null guard.
    """

    complaint: str | None = Field(default=None, max_length=1000)
    odometer_km: int | None = Field(default=None, ge=0, le=MAX_ODOMETER_KM)
    notes: str | None = None


class WorkOrderStatusUpdateRequest(BaseModel):
    """`PUT /work-orders/{id}/status` body (`design.md`'s AD-7): an
    idempotent `PUT` of a target status over the acyclic machine.
    """

    status: WorkOrderStatus


class WorkOrderLineCreateRequest(BaseModel):
    id: uuid.UUID
    kind: Literal["labor", "inventory_part", "external_part"]
    item_id: uuid.UUID | None = None
    description: str = Field(min_length=1, max_length=200)
    quantity: int = Field(ge=1, le=10_000)
    unit_price_cents: int = Field(ge=0, le=1_000_000_000)

    @model_validator(mode="after")
    def _item_matches_kind(self) -> "WorkOrderLineCreateRequest":
        """Mirrors `ck_work_order_lines_item_matches_kind`: an
        `inventory_part` line must reference an item, and no other kind
        may.
        """
        if (self.kind == "inventory_part") != (self.item_id is not None):
            raise ValueError("item_id is required for inventory_part lines only")
        return self


class WorkOrderLineUpdateRequest(BaseModel):
    """`kind` and `item_id` are intentionally absent: a line's part is
    immutable after creation (see the `work-orders` capability spec).
    """

    description: str | None = Field(default=None, min_length=1, max_length=200)
    quantity: int | None = Field(default=None, ge=1, le=10_000)
    unit_price_cents: int | None = Field(default=None, ge=0, le=1_000_000_000)

    @field_validator("description")
    @classmethod
    def _reject_null_description(cls, value: str | None) -> str:
        """Reject an explicit `description: null` (mirrors
        `CustomerUpdateRequest._reject_null_full_name`): without this
        guard the `None` union branch bypasses `min_length`, and
        `update_line` would crash calling `.strip()` on `None`.
        """
        if value is None:
            raise ValueError("description cannot be null")
        return value

    @field_validator("quantity")
    @classmethod
    def _reject_null_quantity(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("quantity cannot be null")
        return value

    @field_validator("unit_price_cents")
    @classmethod
    def _reject_null_unit_price(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("unit_price_cents cannot be null")
        return value


class WorkOrderVehicleOut(BaseModel):
    id: uuid.UUID
    vehicle_type: VehicleType
    make: str
    model: str | None
    year: int | None
    plate: str | None

    @classmethod
    def from_domain(cls, vehicle: Vehicle) -> "WorkOrderVehicleOut":
        return cls(
            id=vehicle.id,
            vehicle_type=vehicle.vehicle_type,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            plate=vehicle.plate,
        )


class WorkOrderCustomerOut(BaseModel):
    id: uuid.UUID
    full_name: str

    @classmethod
    def from_domain(cls, customer: Customer) -> "WorkOrderCustomerOut":
        return cls(id=customer.id, full_name=customer.full_name)


class WorkOrderCustomerDetailOut(WorkOrderCustomerOut):
    phone: str | None
    phone_is_mobile: bool | None

    @classmethod
    def from_domain(cls, customer: Customer) -> "WorkOrderCustomerDetailOut":  # type: ignore[override]
        return cls(
            id=customer.id,
            full_name=customer.full_name,
            phone=customer.phone,
            phone_is_mobile=customer.phone_is_mobile,
        )


class WorkOrderLineOut(BaseModel):
    id: uuid.UUID
    kind: LineKind
    item_id: uuid.UUID | None
    description: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int
    stock_posted_quantity: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, line: WorkOrderLine) -> "WorkOrderLineOut":
        return cls(
            id=line.id,
            kind=line.kind,
            item_id=line.item_id,
            description=line.description,
            quantity=line.quantity,
            unit_price_cents=line.unit_price_cents,
            line_total_cents=line_subtotal_cents(line),
            stock_posted_quantity=line.stock_posted_quantity,
            created_at=line.created_at,
            updated_at=line.updated_at,
        )


class WorkOrderSummaryOut(BaseModel):
    id: uuid.UUID
    number: int
    status: WorkOrderStatus
    vehicle: WorkOrderVehicleOut
    customer: WorkOrderCustomerOut
    total_cents: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(
        cls, order: WorkOrder, *, vehicle: Vehicle, customer: Customer, total_cents: int
    ) -> "WorkOrderSummaryOut":
        return cls(
            id=order.id,
            number=order.number,
            status=order.status,
            vehicle=WorkOrderVehicleOut.from_domain(vehicle),
            customer=WorkOrderCustomerOut.from_domain(customer),
            total_cents=total_cents,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


class WorkOrderOut(BaseModel):
    id: uuid.UUID
    number: int
    status: WorkOrderStatus
    vehicle: WorkOrderVehicleOut
    customer: WorkOrderCustomerDetailOut
    complaint: str | None
    odometer_km: int | None
    notes: str | None
    lines: list[WorkOrderLineOut]
    total_cents: int
    allowed_transitions: list[WorkOrderStatus]
    lines_editable: bool
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    delivered_at: datetime | None
    cancelled_at: datetime | None

    @classmethod
    def from_domain(
        cls, order: WorkOrder, *, vehicle: Vehicle, customer: Customer
    ) -> "WorkOrderOut":
        return cls(
            id=order.id,
            number=order.number,
            status=order.status,
            vehicle=WorkOrderVehicleOut.from_domain(vehicle),
            customer=WorkOrderCustomerDetailOut.from_domain(customer),
            complaint=order.complaint,
            odometer_km=order.odometer_km,
            notes=order.notes,
            lines=[
                WorkOrderLineOut.from_domain(line)
                for line in order.lines
                if line.removed_at is None
            ],
            total_cents=order_total_cents(order.lines),
            allowed_transitions=sorted(TRANSITIONS[order.status]),
            lines_editable=order.status in EDITABLE,
            created_at=order.created_at,
            updated_at=order.updated_at,
            approved_at=order.approved_at,
            started_at=order.started_at,
            completed_at=order.completed_at,
            delivered_at=order.delivered_at,
            cancelled_at=order.cancelled_at,
        )

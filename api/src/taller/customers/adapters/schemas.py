"""Pydantic request/response schemas for the customers HTTP API.

Unlike `taller.inventory.adapters.schemas`' name validator, the phone field
here has no Pydantic `field_validator`: identity has no reusable
`invalid_phone` detail code at the HTTP layer (only the `PhoneNumber` value
object itself), so this feature mints its own `detail: "invalid_phone"`
mapping by catching `InvalidPhoneNumber` directly in the router, from the
exception the use case layer raises. A Pydantic validator here would
instead produce FastAPI's generic validation-error body.
"""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from taller.customers.domain.entities import Customer, Vehicle, VehicleType

#: Design's bound for a vehicle's model year: 1900 to current year + 1.
_MAX_VEHICLE_YEAR = datetime.now(UTC).year + 1


class CustomerCreateRequest(BaseModel):
    id: uuid.UUID | None = None
    full_name: str = Field(min_length=1, max_length=120)
    phone: str | None = None
    notes: str | None = None


class CustomerUpdateRequest(BaseModel):
    """Only explicitly set fields are applied; an explicit `null` clears
    `phone` or `notes`.
    """

    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = None
    notes: str | None = None


class CustomerOut(BaseModel):
    id: uuid.UUID
    full_name: str
    phone: str | None
    phone_is_mobile: bool | None
    notes: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, customer: Customer) -> "CustomerOut":
        return cls(
            id=customer.id,
            full_name=customer.full_name,
            phone=customer.phone,
            phone_is_mobile=customer.phone_is_mobile,
            notes=customer.notes,
            archived_at=customer.archived_at,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )


class VehicleCreateRequest(BaseModel):
    id: uuid.UUID | None = None
    customer_id: uuid.UUID
    vehicle_type: VehicleType
    make: str = Field(min_length=1, max_length=60)
    model: str | None = Field(default=None, max_length=60)
    year: int | None = Field(default=None, ge=1900, le=_MAX_VEHICLE_YEAR)
    color: str | None = Field(default=None, max_length=30)
    plate: str | None = None
    notes: str | None = None


class VehicleUpdateRequest(BaseModel):
    """`customer_id` is intentionally absent: a vehicle's owner never
    changes after creation (see the vehicles capability spec).
    """

    vehicle_type: VehicleType | None = None
    make: str | None = Field(default=None, min_length=1, max_length=60)
    model: str | None = Field(default=None, max_length=60)
    year: int | None = Field(default=None, ge=1900, le=_MAX_VEHICLE_YEAR)
    color: str | None = Field(default=None, max_length=30)
    plate: str | None = None
    notes: str | None = None


class VehicleOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    vehicle_type: VehicleType
    make: str
    model: str | None
    year: int | None
    color: str | None
    plate: str | None
    notes: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, vehicle: Vehicle) -> "VehicleOut":
        return cls(
            id=vehicle.id,
            customer_id=vehicle.customer_id,
            vehicle_type=vehicle.vehicle_type,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color,
            plate=vehicle.plate,
            notes=vehicle.notes,
            archived_at=vehicle.archived_at,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at,
        )


class VehicleDetailOut(VehicleOut):
    owner: CustomerOut

    @classmethod
    def from_domain(cls, vehicle: Vehicle, owner: Customer) -> "VehicleDetailOut":  # type: ignore[override]
        return cls(
            **VehicleOut.from_domain(vehicle).model_dump(), owner=CustomerOut.from_domain(owner)
        )

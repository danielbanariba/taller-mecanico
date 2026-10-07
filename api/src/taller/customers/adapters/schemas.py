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
from datetime import datetime

from pydantic import BaseModel, Field

from taller.customers.domain.entities import Customer


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

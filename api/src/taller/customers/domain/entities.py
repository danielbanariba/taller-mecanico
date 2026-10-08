"""Domain entities for the customers feature: customers and their vehicles."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class VehicleType(StrEnum):
    """The kind of vehicle a customer owns."""

    car = "car"
    motorcycle = "motorcycle"
    other = "other"


@dataclass(slots=True)
class Customer:
    """A workshop's customer.

    ``phone`` stores only the normalized 8 digits from the identity
    feature's ``PhoneNumber`` value object (AD-8). A customer's phone and a
    user's login phone are otherwise unrelated data; this entity just
    reuses the same normalization rule, unchanged.

    ``billing_name`` (razón social) and ``rtn`` are optional fiscal fields
    (`sar-invoicing`'s `customers` delta, AD-11): both are ``None`` until a
    workshop needs them to identify a buyer on a Factura. ``rtn`` stores
    only the normalized 14 digits from ``taller.customers.domain.rtn.Rtn``.
    """

    id: uuid.UUID
    workshop_id: uuid.UUID
    full_name: str
    phone: str | None
    notes: str | None
    billing_name: str | None
    rtn: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def phone_is_mobile(self) -> bool | None:
        """Whether the phone is a mobile number, or ``None`` with no phone.

        A normalized first digit of ``2`` is a landline; any other digit
        `PhoneNumber` accepts (3-9) is a mobile (AD-8). Derived from the
        stored phone rather than persisted separately, so it can never
        drift from it.
        """
        if self.phone is None:
            return None
        return self.phone[0] != "2"


@dataclass(slots=True)
class Vehicle:
    """A vehicle owned by one customer.

    ``plate`` stores only the normalized form (see
    ``taller.customers.domain.plate.normalize_plate``, added in slice 2),
    unique per workshop among active vehicles. Declared alongside
    ``Customer`` because the phase-1 migration creates both tables
    together; the vehicle use cases themselves land in slice 2.
    """

    id: uuid.UUID
    workshop_id: uuid.UUID
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

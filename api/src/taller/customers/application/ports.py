"""Ports the customers use cases depend on, implemented by adapters."""

import uuid
from typing import Protocol

from taller.customers.domain.entities import Customer, Vehicle


class CustomerRepository(Protocol):
    def get_by_id(self, *, workshop_id: uuid.UUID, customer_id: uuid.UUID) -> Customer | None: ...

    def get_for_update(self, *, workshop_id: uuid.UUID, customer_id: uuid.UUID) -> Customer | None:
        """Like :meth:`get_by_id`, but locks the row (``SELECT ... FOR
        UPDATE``) so archiving a customer and creating a vehicle for that
        same customer serialize instead of racing: whichever transaction
        gets there first holds the lock until it commits, so the other
        always re-reads the committed `archived_at` state (mirrors
        `taller.inventory.application.ports.ItemRepository.get_for_update`).
        """
        ...

    def add(self, customer: Customer) -> None: ...

    def save(self, customer: Customer) -> None:
        """Persist every mutable field of an already-existing customer."""
        ...

    def list(
        self, *, workshop_id: uuid.UUID, query: str | None, include_archived: bool
    ) -> list[Customer]: ...


class VehicleRepository(Protocol):
    """Implemented starting slice 2 (`SqlAlchemyVehicleRepository`).

    Declared now because the phase-1 migration creates the `vehicles`
    table together with `customers`, and `CustomerRepository` /
    `VehicleRepository` are meant to land as a pair.
    """

    def get_by_id(self, *, workshop_id: uuid.UUID, vehicle_id: uuid.UUID) -> Vehicle | None: ...

    def get_many(self, *, workshop_id: uuid.UUID, vehicle_ids: list[uuid.UUID]) -> list[Vehicle]:
        """Batched lookup for phase 2's `describe_vehicles` (AD-12)."""
        ...

    def get_active_by_plate(
        self, *, workshop_id: uuid.UUID, plate: str, exclude_id: uuid.UUID | None = None
    ) -> Vehicle | None:
        """The active vehicle whose normalized plate matches, if any,
        excluding ``exclude_id`` (checked when editing a vehicle's own
        plate, so it never collides with itself).
        """
        ...

    def add(self, vehicle: Vehicle) -> None: ...

    def save(self, vehicle: Vehicle) -> None:
        """Persist every mutable field of an already-existing vehicle."""
        ...

    def list_for_customer(
        self, *, workshop_id: uuid.UUID, customer_id: uuid.UUID, include_archived: bool
    ) -> list[Vehicle]: ...

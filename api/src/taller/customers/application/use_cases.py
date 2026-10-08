"""Use cases for the customers feature: customers and their vehicles."""

import uuid
from datetime import UTC, datetime

from taller.customers.application.ports import CustomerRepository, VehicleRepository
from taller.customers.domain.entities import Customer, Vehicle, VehicleType
from taller.customers.domain.errors import (
    CustomerIdConflict,
    CustomerNotFound,
    PlateTaken,
    VehicleIdConflict,
    VehicleNotFound,
)
from taller.customers.domain.plate import normalize_plate
from taller.customers.domain.rtn import Rtn
from taller.identity.domain.phone_number import PhoneNumber


def _normalize_optional_text(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip()
    return cleaned or None


def _normalize_phone(raw: str | None) -> str | None:
    """Normalize an optional phone through identity's `PhoneNumber` (AD-8).

    Raises:
        InvalidPhoneNumber: ``raw`` is present but not a valid Honduran
            phone number.
    """
    if raw is None:
        return None
    return PhoneNumber.from_raw(raw).value


def _normalize_rtn(raw: str | None) -> str | None:
    """Normalize an optional RTN through `Rtn.from_raw` (AD-11).

    Raises:
        InvalidRtn: ``raw`` is present but not a valid 14-digit RTN.
    """
    if raw is None:
        return None
    return Rtn.from_raw(raw)


def _customer_fields_match(
    customer: Customer,
    *,
    full_name: str,
    phone: str | None,
    notes: str | None,
    billing_name: str | None,
    rtn: str | None,
) -> bool:
    return (
        customer.full_name == full_name
        and customer.phone == phone
        and customer.notes == notes
        and customer.billing_name == billing_name
        and customer.rtn == rtn
    )


def create_customer(
    *,
    workshop_id: uuid.UUID,
    customer_id: uuid.UUID | None,
    full_name: str,
    phone: str | None,
    notes: str | None,
    billing_name: str | None = None,
    rtn: str | None = None,
    customer_repo: CustomerRepository,
) -> tuple[Customer, bool]:
    """Create a customer, or replay an idempotent create.

    ``billing_name`` and ``rtn`` are fiscal fields (`sar-invoicing`'s
    `customers` delta): both optional, and both participate in the
    replay comparison below exactly like every other field.

    Returns ``(customer, is_new)``: ``is_new`` is False when ``customer_id``
    already existed with identical fields (the caller should respond 200,
    not 201).

    Raises:
        InvalidPhoneNumber: ``phone`` is present but not a valid Honduran
            phone number.
        InvalidRtn: ``rtn`` is present but not a valid 14-digit RTN.
        CustomerIdConflict: ``customer_id`` already exists with different
            fields.
    """
    normalized_name = full_name.strip()
    normalized_phone = _normalize_phone(phone)
    normalized_notes = _normalize_optional_text(notes)
    normalized_billing_name = _normalize_optional_text(billing_name)
    normalized_rtn = _normalize_rtn(rtn)

    if customer_id is not None:
        existing = customer_repo.get_by_id(workshop_id=workshop_id, customer_id=customer_id)
        if existing is not None:
            if not _customer_fields_match(
                existing,
                full_name=normalized_name,
                phone=normalized_phone,
                notes=normalized_notes,
                billing_name=normalized_billing_name,
                rtn=normalized_rtn,
            ):
                raise CustomerIdConflict(customer_id)
            return existing, False

    now = datetime.now(UTC)
    customer = Customer(
        id=customer_id if customer_id is not None else uuid.uuid4(),
        workshop_id=workshop_id,
        full_name=normalized_name,
        phone=normalized_phone,
        notes=normalized_notes,
        billing_name=normalized_billing_name,
        rtn=normalized_rtn,
        archived_at=None,
        created_at=now,
        updated_at=now,
    )
    customer_repo.add(customer)
    return customer, True


def get_customer(
    *, workshop_id: uuid.UUID, customer_id: uuid.UUID, customer_repo: CustomerRepository
) -> Customer:
    """Raises: CustomerNotFound: no such customer in this workshop."""
    customer = customer_repo.get_by_id(workshop_id=workshop_id, customer_id=customer_id)
    if customer is None:
        raise CustomerNotFound(customer_id)
    return customer


def list_customers(
    *,
    workshop_id: uuid.UUID,
    query: str | None,
    include_archived: bool,
    customer_repo: CustomerRepository,
) -> list[Customer]:
    cleaned_query = query.strip() if query else None
    return customer_repo.list(
        workshop_id=workshop_id, query=cleaned_query or None, include_archived=include_archived
    )


def update_customer(
    *,
    workshop_id: uuid.UUID,
    customer_id: uuid.UUID,
    fields: dict,
    customer_repo: CustomerRepository,
) -> Customer:
    """Update any customer field present in ``fields``.

    ``fields`` only contains keys the caller explicitly set (e.g. via
    Pydantic's ``exclude_unset``), so omitted fields are left untouched and
    an explicit null clears an optional field (phone, notes, billing_name,
    or rtn).

    Raises:
        CustomerNotFound: no such customer in this workshop.
        InvalidPhoneNumber: ``fields["phone"]`` is present but invalid.
        InvalidRtn: ``fields["rtn"]`` is present but invalid.
    """
    customer = customer_repo.get_by_id(workshop_id=workshop_id, customer_id=customer_id)
    if customer is None:
        raise CustomerNotFound(customer_id)

    if "full_name" in fields:
        customer.full_name = fields["full_name"].strip()
    if "phone" in fields:
        customer.phone = _normalize_phone(fields["phone"])
    if "notes" in fields:
        customer.notes = _normalize_optional_text(fields["notes"])
    if "billing_name" in fields:
        customer.billing_name = _normalize_optional_text(fields["billing_name"])
    if "rtn" in fields:
        customer.rtn = _normalize_rtn(fields["rtn"])

    customer.updated_at = datetime.now(UTC)
    customer_repo.save(customer)
    return customer


def archive_customer(
    *,
    workshop_id: uuid.UUID,
    customer_id: uuid.UUID,
    customer_repo: CustomerRepository,
    vehicle_repo: VehicleRepository,
) -> None:
    """Raises: CustomerNotFound: no such customer in this workshop.

    Cascades to every active vehicle owned by the customer, stamped with
    the customer's own `archived_at` timestamp (AD-15), which frees each
    of those vehicles' plates for reuse. An already-archived vehicle is
    left untouched.

    Locks the customer row (`get_for_update`) before checking and changing
    its state, so a concurrent `create_vehicle` for the same customer can't
    interleave between this archive's check and its write and leave a new
    vehicle active under a customer that is (or is about to be) archived.
    """
    customer = customer_repo.get_for_update(workshop_id=workshop_id, customer_id=customer_id)
    if customer is None:
        raise CustomerNotFound(customer_id)
    if customer.archived_at is None:
        now = datetime.now(UTC)
        customer.archived_at = now
        customer.updated_at = now
        customer_repo.save(customer)
        for vehicle in vehicle_repo.list_for_customer(
            workshop_id=workshop_id, customer_id=customer_id, include_archived=False
        ):
            vehicle.archived_at = now
            vehicle.updated_at = now
            vehicle_repo.save(vehicle)


def _vehicle_fields_match(
    vehicle: Vehicle,
    *,
    customer_id: uuid.UUID,
    vehicle_type: VehicleType,
    make: str,
    model: str | None,
    year: int | None,
    color: str | None,
    plate: str | None,
    notes: str | None,
) -> bool:
    return (
        vehicle.customer_id == customer_id
        and vehicle.vehicle_type == vehicle_type
        and vehicle.make == make
        and vehicle.model == model
        and vehicle.year == year
        and vehicle.color == color
        and vehicle.plate == plate
        and vehicle.notes == notes
    )


def create_vehicle(
    *,
    workshop_id: uuid.UUID,
    vehicle_id: uuid.UUID | None,
    customer_id: uuid.UUID,
    vehicle_type: VehicleType,
    make: str,
    model: str | None,
    year: int | None,
    color: str | None,
    plate: str | None,
    notes: str | None,
    customer_repo: CustomerRepository,
    vehicle_repo: VehicleRepository,
) -> tuple[Vehicle, bool]:
    """Create a vehicle, or replay an idempotent create.

    Replay detection runs before the owner check and the plate-uniqueness
    check (AD-14): a replayed plated vehicle must not re-trigger
    `PlateTaken` against itself.

    Returns ``(vehicle, is_new)``: ``is_new`` is False when ``vehicle_id``
    already existed with identical fields (the caller should respond 200,
    not 201).

    Raises:
        InvalidPlate: ``plate`` is present but does not normalize to a
            valid plate.
        VehicleIdConflict: ``vehicle_id`` already exists with different
            fields.
        CustomerNotFound: no active customer ``customer_id`` in this
            workshop (also raised for an archived customer: new links to
            an archived customer are refused).
        PlateTaken: another active vehicle in the workshop already has
            this normalized plate.
    """
    normalized_make = make.strip()
    normalized_model = _normalize_optional_text(model)
    normalized_color = _normalize_optional_text(color)
    normalized_plate = normalize_plate(plate)
    normalized_notes = _normalize_optional_text(notes)

    if vehicle_id is not None:
        existing = vehicle_repo.get_by_id(workshop_id=workshop_id, vehicle_id=vehicle_id)
        if existing is not None:
            if not _vehicle_fields_match(
                existing,
                customer_id=customer_id,
                vehicle_type=vehicle_type,
                make=normalized_make,
                model=normalized_model,
                year=year,
                color=normalized_color,
                plate=normalized_plate,
                notes=normalized_notes,
            ):
                raise VehicleIdConflict(vehicle_id)
            return existing, False

    # Locks the owner row (`get_for_update`) before checking it is active,
    # so a concurrent `archive_customer` for the same customer can't
    # interleave between this check and the vehicle insert and leave a new
    # vehicle active under a customer that is being archived right now.
    owner = customer_repo.get_for_update(workshop_id=workshop_id, customer_id=customer_id)
    if owner is None or owner.archived_at is not None:
        raise CustomerNotFound(customer_id)

    if normalized_plate is not None:
        collision = vehicle_repo.get_active_by_plate(
            workshop_id=workshop_id, plate=normalized_plate
        )
        if collision is not None:
            raise PlateTaken(normalized_plate)

    now = datetime.now(UTC)
    vehicle = Vehicle(
        id=vehicle_id if vehicle_id is not None else uuid.uuid4(),
        workshop_id=workshop_id,
        customer_id=customer_id,
        vehicle_type=vehicle_type,
        make=normalized_make,
        model=normalized_model,
        year=year,
        color=normalized_color,
        plate=normalized_plate,
        notes=normalized_notes,
        archived_at=None,
        created_at=now,
        updated_at=now,
    )
    vehicle_repo.add(vehicle)
    return vehicle, True


def get_vehicle(
    *, workshop_id: uuid.UUID, vehicle_id: uuid.UUID, vehicle_repo: VehicleRepository
) -> Vehicle:
    """Raises: VehicleNotFound: no such vehicle in this workshop."""
    vehicle = vehicle_repo.get_by_id(workshop_id=workshop_id, vehicle_id=vehicle_id)
    if vehicle is None:
        raise VehicleNotFound(vehicle_id)
    return vehicle


def list_vehicles_for_customer(
    *,
    workshop_id: uuid.UUID,
    customer_id: uuid.UUID,
    include_archived: bool,
    customer_repo: CustomerRepository,
    vehicle_repo: VehicleRepository,
) -> list[Vehicle]:
    """Raises: CustomerNotFound: no such customer in this workshop."""
    customer = customer_repo.get_by_id(workshop_id=workshop_id, customer_id=customer_id)
    if customer is None:
        raise CustomerNotFound(customer_id)
    return vehicle_repo.list_for_customer(
        workshop_id=workshop_id, customer_id=customer_id, include_archived=include_archived
    )


def update_vehicle(
    *,
    workshop_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    fields: dict,
    vehicle_repo: VehicleRepository,
) -> Vehicle:
    """Update any editable vehicle field present in ``fields``.

    ``customer_id`` is never one of ``fields``: the HTTP schema layer does
    not expose it, because a vehicle's owner is immutable after creation.

    Raises:
        VehicleNotFound: no such vehicle in this workshop.
        InvalidPlate: ``fields["plate"]`` is present but invalid.
        PlateTaken: the new normalized plate collides with another active
            vehicle in the workshop.
    """
    vehicle = vehicle_repo.get_by_id(workshop_id=workshop_id, vehicle_id=vehicle_id)
    if vehicle is None:
        raise VehicleNotFound(vehicle_id)

    if "vehicle_type" in fields:
        vehicle.vehicle_type = fields["vehicle_type"]
    if "make" in fields:
        vehicle.make = fields["make"].strip()
    if "model" in fields:
        vehicle.model = _normalize_optional_text(fields["model"])
    if "year" in fields:
        vehicle.year = fields["year"]
    if "color" in fields:
        vehicle.color = _normalize_optional_text(fields["color"])
    if "plate" in fields:
        new_plate = normalize_plate(fields["plate"])
        if new_plate != vehicle.plate and new_plate is not None:
            collision = vehicle_repo.get_active_by_plate(
                workshop_id=workshop_id, plate=new_plate, exclude_id=vehicle.id
            )
            if collision is not None:
                raise PlateTaken(new_plate)
        vehicle.plate = new_plate
    if "notes" in fields:
        vehicle.notes = _normalize_optional_text(fields["notes"])

    vehicle.updated_at = datetime.now(UTC)
    vehicle_repo.save(vehicle)
    return vehicle


def archive_vehicle(
    *, workshop_id: uuid.UUID, vehicle_id: uuid.UUID, vehicle_repo: VehicleRepository
) -> None:
    """Raises: VehicleNotFound: no such vehicle in this workshop."""
    vehicle = vehicle_repo.get_by_id(workshop_id=workshop_id, vehicle_id=vehicle_id)
    if vehicle is None:
        raise VehicleNotFound(vehicle_id)
    if vehicle.archived_at is None:
        now = datetime.now(UTC)
        vehicle.archived_at = now
        vehicle.updated_at = now
        vehicle_repo.save(vehicle)


def get_active_vehicle(
    *, workshop_id: uuid.UUID, vehicle_id: uuid.UUID, vehicle_repo: VehicleRepository
) -> Vehicle:
    """Resolve a vehicle a new work order may reference (phase 2's AD-12).

    Raises:
        VehicleNotFound: no such vehicle in this workshop, or it is
            archived. Archived vehicles cannot receive new links, the same
            rule AD-14 already applies to an archived customer.
    """
    vehicle = vehicle_repo.get_by_id(workshop_id=workshop_id, vehicle_id=vehicle_id)
    if vehicle is None or vehicle.archived_at is not None:
        raise VehicleNotFound(vehicle_id)
    return vehicle


def describe_vehicles(
    *,
    workshop_id: uuid.UUID,
    vehicle_ids: list[uuid.UUID],
    vehicle_repo: VehicleRepository,
    customer_repo: CustomerRepository,
) -> dict[uuid.UUID, tuple[Vehicle, Customer]]:
    """Batch-resolve vehicles and their owners for a work-order list or
    detail response (`design.md`'s AD-12).

    Two queries total, however many ids are passed: one against
    `vehicles`, one against `customers`. Never a per-order round trip, and
    never a join across the two features' tables. An archived vehicle (or
    one owned by an archived customer) is still resolved: an existing
    order must keep displaying it, even though AD-14 forbids a *new* link
    to one.

    An id with no matching vehicle, or whose owner cannot be resolved
    (should not happen for a vehicle a work order already references), is
    simply absent from the result; callers decide how to handle a gap.
    """
    unique_vehicle_ids = list(dict.fromkeys(vehicle_ids))
    if not unique_vehicle_ids:
        return {}
    vehicles = vehicle_repo.get_many(workshop_id=workshop_id, vehicle_ids=unique_vehicle_ids)
    customer_ids = list(dict.fromkeys(vehicle.customer_id for vehicle in vehicles))
    customers_by_id = {
        customer.id: customer
        for customer in customer_repo.get_many(workshop_id=workshop_id, customer_ids=customer_ids)
    }
    result: dict[uuid.UUID, tuple[Vehicle, Customer]] = {}
    for vehicle in vehicles:
        owner = customers_by_id.get(vehicle.customer_id)
        if owner is not None:
            result[vehicle.id] = (vehicle, owner)
    return result

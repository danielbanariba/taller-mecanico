"""Use cases for the customers feature: customer records.

Vehicle use cases land in slice 2, once `VehicleRepository` has a real
implementation.
"""

import uuid
from datetime import UTC, datetime

from taller.customers.application.ports import CustomerRepository
from taller.customers.domain.entities import Customer
from taller.customers.domain.errors import CustomerIdConflict, CustomerNotFound
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


def _customer_fields_match(
    customer: Customer, *, full_name: str, phone: str | None, notes: str | None
) -> bool:
    return customer.full_name == full_name and customer.phone == phone and customer.notes == notes


def create_customer(
    *,
    workshop_id: uuid.UUID,
    customer_id: uuid.UUID | None,
    full_name: str,
    phone: str | None,
    notes: str | None,
    customer_repo: CustomerRepository,
) -> tuple[Customer, bool]:
    """Create a customer, or replay an idempotent create.

    Returns ``(customer, is_new)``: ``is_new`` is False when ``customer_id``
    already existed with identical fields (the caller should respond 200,
    not 201).

    Raises:
        InvalidPhoneNumber: ``phone`` is present but not a valid Honduran
            phone number.
        CustomerIdConflict: ``customer_id`` already exists with different
            fields.
    """
    normalized_name = full_name.strip()
    normalized_phone = _normalize_phone(phone)
    normalized_notes = _normalize_optional_text(notes)

    if customer_id is not None:
        existing = customer_repo.get_by_id(workshop_id=workshop_id, customer_id=customer_id)
        if existing is not None:
            if not _customer_fields_match(
                existing, full_name=normalized_name, phone=normalized_phone, notes=normalized_notes
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
    an explicit null clears an optional field (phone or notes).

    Raises:
        CustomerNotFound: no such customer in this workshop.
        InvalidPhoneNumber: ``fields["phone"]`` is present but invalid.
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

    customer.updated_at = datetime.now(UTC)
    customer_repo.save(customer)
    return customer


def archive_customer(
    *, workshop_id: uuid.UUID, customer_id: uuid.UUID, customer_repo: CustomerRepository
) -> None:
    """Raises: CustomerNotFound: no such customer in this workshop.

    Slice 2 extends this to also cascade to the customer's active vehicles
    (AD-15); this slice only archives the customer itself.
    """
    customer = customer_repo.get_by_id(workshop_id=workshop_id, customer_id=customer_id)
    if customer is None:
        raise CustomerNotFound(customer_id)
    if customer.archived_at is None:
        now = datetime.now(UTC)
        customer.archived_at = now
        customer.updated_at = now
        customer_repo.save(customer)

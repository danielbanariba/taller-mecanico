"""SQLAlchemy-backed adapters for the customers ports."""

import uuid

from sqlalchemy import and_, exists, func, or_
from sqlalchemy.orm import Session

from taller.customers.adapters.models import CustomerModel, VehicleModel
from taller.customers.domain.entities import Customer, Vehicle, VehicleType


def _customer_from_model(model: CustomerModel) -> Customer:
    return Customer(
        id=model.id,
        workshop_id=model.workshop_id,
        full_name=model.full_name,
        phone=model.phone,
        notes=model.notes,
        archived_at=model.archived_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


#: Character used to escape `%`/`_` when building a `LIKE` pattern from a
#: user-supplied search term, mirroring
#: `taller.inventory.adapters.repositories._escape_like`.
_LIKE_ESCAPE_CHAR = "\\"


def _escape_like(raw: str) -> str:
    """Escape `LIKE` metacharacters so `raw` matches only literally."""
    escaped = raw.replace(_LIKE_ESCAPE_CHAR, _LIKE_ESCAPE_CHAR * 2)
    escaped = escaped.replace("%", f"{_LIKE_ESCAPE_CHAR}%")
    return escaped.replace("_", f"{_LIKE_ESCAPE_CHAR}_")


class SqlAlchemyCustomerRepository:
    """Customer persistence backed by SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, *, workshop_id: uuid.UUID, customer_id: uuid.UUID) -> Customer | None:
        model = (
            self._session.query(CustomerModel)
            .filter(CustomerModel.id == customer_id, CustomerModel.workshop_id == workshop_id)
            .one_or_none()
        )
        return _customer_from_model(model) if model is not None else None

    def add(self, customer: Customer) -> None:
        self._session.add(
            CustomerModel(
                id=customer.id,
                workshop_id=customer.workshop_id,
                full_name=customer.full_name,
                phone=customer.phone,
                notes=customer.notes,
                archived_at=customer.archived_at,
                created_at=customer.created_at,
                updated_at=customer.updated_at,
            )
        )
        self._session.flush()

    def save(self, customer: Customer) -> None:
        model = self._session.get(CustomerModel, customer.id)
        if model is None:
            return
        model.full_name = customer.full_name
        model.phone = customer.phone
        model.notes = customer.notes
        model.archived_at = customer.archived_at
        model.updated_at = customer.updated_at
        self._session.flush()

    def list(
        self, *, workshop_id: uuid.UUID, query: str | None, include_archived: bool
    ) -> list[Customer]:
        q = self._session.query(CustomerModel).filter(CustomerModel.workshop_id == workshop_id)
        if not include_archived:
            q = q.filter(CustomerModel.archived_at.is_(None))
        if query:
            pattern = func.taller_unaccent_lower(f"%{_escape_like(query)}%")
            plate_pattern = f"%{_escape_like(query.upper())}%"
            # A correlated EXISTS, not a join, so a customer with several
            # matching vehicles is never returned as duplicate rows.
            plate_match = exists().where(
                and_(
                    VehicleModel.customer_id == CustomerModel.id,
                    VehicleModel.workshop_id == workshop_id,
                    VehicleModel.archived_at.is_(None),
                    VehicleModel.plate.isnot(None),
                    VehicleModel.plate.like(plate_pattern, escape=_LIKE_ESCAPE_CHAR),
                )
            )
            q = q.filter(
                or_(
                    func.taller_unaccent_lower(CustomerModel.full_name).like(
                        pattern, escape=_LIKE_ESCAPE_CHAR
                    ),
                    CustomerModel.phone.like(f"%{_escape_like(query)}%", escape=_LIKE_ESCAPE_CHAR),
                    plate_match,
                )
            )
        q = q.order_by(func.taller_unaccent_lower(CustomerModel.full_name).asc(), CustomerModel.id)
        return [_customer_from_model(model) for model in q.all()]


def _vehicle_from_model(model: VehicleModel) -> Vehicle:
    return Vehicle(
        id=model.id,
        workshop_id=model.workshop_id,
        customer_id=model.customer_id,
        vehicle_type=VehicleType(model.vehicle_type),
        make=model.make,
        model=model.model,
        year=model.year,
        color=model.color,
        plate=model.plate,
        notes=model.notes,
        archived_at=model.archived_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyVehicleRepository:
    """Vehicle persistence backed by SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, *, workshop_id: uuid.UUID, vehicle_id: uuid.UUID) -> Vehicle | None:
        model = (
            self._session.query(VehicleModel)
            .filter(VehicleModel.id == vehicle_id, VehicleModel.workshop_id == workshop_id)
            .one_or_none()
        )
        return _vehicle_from_model(model) if model is not None else None

    def get_many(self, *, workshop_id: uuid.UUID, vehicle_ids: list[uuid.UUID]) -> list[Vehicle]:
        if not vehicle_ids:
            return []
        models = (
            self._session.query(VehicleModel)
            .filter(VehicleModel.workshop_id == workshop_id, VehicleModel.id.in_(vehicle_ids))
            .all()
        )
        return [_vehicle_from_model(model) for model in models]

    def get_active_by_plate(
        self, *, workshop_id: uuid.UUID, plate: str, exclude_id: uuid.UUID | None = None
    ) -> Vehicle | None:
        q = self._session.query(VehicleModel).filter(
            VehicleModel.workshop_id == workshop_id,
            VehicleModel.plate == plate,
            VehicleModel.archived_at.is_(None),
        )
        if exclude_id is not None:
            q = q.filter(VehicleModel.id != exclude_id)
        model = q.one_or_none()
        return _vehicle_from_model(model) if model is not None else None

    def add(self, vehicle: Vehicle) -> None:
        self._session.add(
            VehicleModel(
                id=vehicle.id,
                workshop_id=vehicle.workshop_id,
                customer_id=vehicle.customer_id,
                vehicle_type=vehicle.vehicle_type.value,
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
        )
        self._session.flush()

    def save(self, vehicle: Vehicle) -> None:
        model = self._session.get(VehicleModel, vehicle.id)
        if model is None:
            return
        model.vehicle_type = vehicle.vehicle_type.value
        model.make = vehicle.make
        model.model = vehicle.model
        model.year = vehicle.year
        model.color = vehicle.color
        model.plate = vehicle.plate
        model.notes = vehicle.notes
        model.archived_at = vehicle.archived_at
        model.updated_at = vehicle.updated_at
        self._session.flush()

    def list_for_customer(
        self, *, workshop_id: uuid.UUID, customer_id: uuid.UUID, include_archived: bool
    ) -> list[Vehicle]:
        q = self._session.query(VehicleModel).filter(
            VehicleModel.workshop_id == workshop_id, VehicleModel.customer_id == customer_id
        )
        if not include_archived:
            q = q.filter(VehicleModel.archived_at.is_(None))
        q = q.order_by(VehicleModel.created_at.asc(), VehicleModel.id)
        return [_vehicle_from_model(model) for model in q.all()]

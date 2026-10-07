"""SQLAlchemy-backed adapters for the customers ports.

`SqlAlchemyVehicleRepository` is added in slice 2, once `VehicleModel` has
application-layer use cases to back.
"""

import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from taller.customers.adapters.models import CustomerModel
from taller.customers.domain.entities import Customer


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
            q = q.filter(
                or_(
                    func.taller_unaccent_lower(CustomerModel.full_name).like(
                        pattern, escape=_LIKE_ESCAPE_CHAR
                    ),
                    CustomerModel.phone.like(f"%{_escape_like(query)}%", escape=_LIKE_ESCAPE_CHAR),
                )
            )
        q = q.order_by(func.taller_unaccent_lower(CustomerModel.full_name).asc(), CustomerModel.id)
        return [_customer_from_model(model) for model in q.all()]

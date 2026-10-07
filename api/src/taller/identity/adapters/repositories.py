"""SQLAlchemy repositories implementing the identity feature's ports.

UUIDs are generated in Python (``uuid.uuid4()``) in the domain/application
layer, so an entity's id exists before it is ever flushed to the database:
a ``Workshop`` and its owner ``User`` can both be built, with the user's
``workshop_id`` already set, before either is sent to the database. ``add()``
still flushes immediately: ``WorkshopModel`` and ``UserModel`` are unrelated
mapper classes with no ORM ``relationship()`` between them, so the unit of
work has no way to know the workshop row must be inserted before the user
row that references it; flushing after each ``add()`` makes that order
explicit instead of leaving it to chance. The HTTP layer still wraps both
flushes in a single ``commit()``, so they land as one transaction.
"""

import uuid

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from taller.identity.adapters.models import LoginThrottleModel, UserModel, WorkshopModel
from taller.identity.domain.entities import User, Workshop
from taller.identity.domain.login_throttle import LoginThrottle
from taller.identity.domain.phone_number import PhoneNumber


def _user_from_model(model: UserModel) -> User:
    return User(
        id=model.id,
        workshop_id=model.workshop_id,
        full_name=model.full_name,
        phone=PhoneNumber(model.phone),
        password_hash=model.password_hash,
        role=model.role,
        created_at=model.created_at,
    )


def _workshop_from_model(model: WorkshopModel) -> Workshop:
    return Workshop(id=model.id, name=model.name, created_at=model.created_at)


class SqlAlchemyUserRepository:
    """User persistence backed by SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_phone(self, phone: PhoneNumber) -> User | None:
        model = self._session.query(UserModel).filter(UserModel.phone == phone.value).one_or_none()
        return _user_from_model(model) if model is not None else None

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        model = self._session.get(UserModel, user_id)
        return _user_from_model(model) if model is not None else None

    def add(self, user: User) -> None:
        self._session.add(
            UserModel(
                id=user.id,
                workshop_id=user.workshop_id,
                full_name=user.full_name,
                phone=user.phone.value,
                password_hash=user.password_hash,
                role=user.role,
                created_at=user.created_at,
            )
        )
        self._session.flush()


class SqlAlchemyWorkshopRepository:
    """Workshop persistence backed by SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, workshop_id: uuid.UUID) -> Workshop | None:
        model = self._session.get(WorkshopModel, workshop_id)
        return _workshop_from_model(model) if model is not None else None

    def add(self, workshop: Workshop) -> None:
        self._session.add(
            WorkshopModel(id=workshop.id, name=workshop.name, created_at=workshop.created_at)
        )
        self._session.flush()


class SqlAlchemyLoginThrottleRepository:
    """Login throttle persistence backed by SQLAlchemy (PostgreSQL only)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_for_update(self, phone: PhoneNumber) -> LoginThrottle:
        # Make sure the row exists before locking it: `SELECT ... FOR UPDATE`
        # locks nothing when there is no row, so two concurrent first
        # attempts for a phone would otherwise both read "no failures" and
        # one increment would be lost. `ON CONFLICT DO NOTHING` never fails
        # on a concurrent insert of the same phone; it waits for it instead.
        self._session.execute(
            insert(LoginThrottleModel)
            .values(phone=phone.value, failed_attempts=0, locked_until=None)
            .on_conflict_do_nothing(index_elements=[LoginThrottleModel.phone])
        )
        model = (
            self._session.query(LoginThrottleModel)
            .filter(LoginThrottleModel.phone == phone.value)
            .with_for_update()
            .populate_existing()
            .one()
        )
        return LoginThrottle(
            phone=phone,
            failed_attempts=model.failed_attempts,
            locked_until=model.locked_until,
        )

    def save(self, throttle: LoginThrottle) -> None:
        model = self._session.get(LoginThrottleModel, throttle.phone.value)
        if model is None:
            return
        model.failed_attempts = throttle.failed_attempts
        model.locked_until = throttle.locked_until
        self._session.flush()

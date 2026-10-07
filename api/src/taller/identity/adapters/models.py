"""SQLAlchemy ORM models for workshops, users, and login throttling."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from taller.shared.db import Base


class WorkshopModel(Base):
    """A repair shop: the tenant every other table is scoped to."""

    __tablename__ = "workshops"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UserModel(Base):
    """A workshop user. Only the ``owner`` role exists for now."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workshops.id"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(8), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default="owner")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LoginThrottleModel(Base):
    """Failed-login bookkeeping per phone number, registered or not.

    Deliberately not a foreign key to ``users``: unregistered phones are
    throttled too, so a lockout never reveals which phones have accounts.
    """

    __tablename__ = "login_throttles"

    phone: Mapped[str] = mapped_column(String(8), primary_key=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

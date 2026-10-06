"""Pydantic request/response schemas for the identity HTTP API."""

import uuid

from pydantic import BaseModel, Field, field_validator

from taller.identity.domain.entities import User, Workshop
from taller.identity.domain.errors import InvalidPhoneNumber
from taller.identity.domain.phone_number import PhoneNumber


def _validate_phone(value: str) -> str:
    """Normalize a phone field, surfacing domain errors as Pydantic ones.

    Raising ``ValueError`` here (instead of catching ``InvalidPhoneNumber``
    in the router) lets FastAPI's own validation machinery turn a malformed
    phone into a 422 response automatically, the same way it already does
    for the password length constraint below.
    """
    try:
        return PhoneNumber.from_raw(value).value
    except InvalidPhoneNumber as exc:
        raise ValueError(str(exc)) from exc


class RegisterRequest(BaseModel):
    workshop_name: str = Field(min_length=1, max_length=200)
    owner_name: str = Field(min_length=1, max_length=200)
    phone: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return _validate_phone(value)


class LoginRequest(BaseModel):
    phone: str
    password: str

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return _validate_phone(value)


class UserOut(BaseModel):
    id: uuid.UUID
    full_name: str
    phone: str
    role: str

    @classmethod
    def from_domain(cls, user: User) -> "UserOut":
        return cls(id=user.id, full_name=user.full_name, phone=user.phone.value, role=user.role)


class WorkshopOut(BaseModel):
    id: uuid.UUID
    name: str

    @classmethod
    def from_domain(cls, workshop: Workshop) -> "WorkshopOut":
        return cls(id=workshop.id, name=workshop.name)


class MeResponse(BaseModel):
    user: UserOut
    workshop: WorkshopOut

    @classmethod
    def from_domain(cls, user: User, workshop: Workshop) -> "MeResponse":
        return cls(user=UserOut.from_domain(user), workshop=WorkshopOut.from_domain(workshop))

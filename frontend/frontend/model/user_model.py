import reflex as rx
from typing import Optional
from sqlmodel import Field


class User(rx.Model, table=True):
    id_user: Optional[int] = Field(default=None, primary_key=True)
    name: str
    username: str
    password: str
    phone: str
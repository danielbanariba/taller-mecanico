import reflex as rx
from typing import Optional
from sqlmodel import Field


class Proveedor(rx.Model, table=True):
    id_proveedor: Optional[int] = Field(default=None, primary_key=True)
    nom_proveedor: str
    id_direccion: Optional[int] = Field(default=None, primary_key=True)
    rtn: str
    id_tel: Optional[int] = Field(default=None, primary_key=True)
    correo: str
    id_vendedor: Optional[int] = Field(default=None, primary_key=True)
    adj_doc: str
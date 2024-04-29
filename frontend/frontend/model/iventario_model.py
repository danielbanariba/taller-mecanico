import reflex as rx
from typing import Optional
from sqlmodel import Field


class Inventario(rx.Model, table=True):
    id_inventario: Optional[int] = Field(default=None, primary_key=True)
    cantidad_productos: Optional[int] = None
    fecha_entrada: Optional[str] = None
    fecha_salida: Optional[str] = None
    id_repuesto: Optional[int] = None
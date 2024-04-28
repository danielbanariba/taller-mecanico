import reflex as rx
from typing import Optional
from sqlmodel import Field


class Inventario(rx.Model, table=True):
    id_inventario: Optional[int] = Field(default=None, primary_key=True)
    cantidad_productos: int
    fecha_entrada: str
    fecha_salida: str
    id_repuesto: int

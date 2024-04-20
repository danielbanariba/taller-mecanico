import reflex as rx
from typing import Optional
from sqlmodel import Field


class Provedor(rx.Model, table=True):
    #ID_PROVEEDOR, NOM_PROVEEDOR, ID_DIRECCION, RTN, ID_TEL, CORREO, ID_VENDEDOR, ADJ_DOC
    id_proveedor: int
    nom_proveedor: str
    id_direccion: int
    rtn: str
    id_tel: int
    correo: str
    id_vendedor: int
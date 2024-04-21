from ..model.proveedor_model import Proveedor
from .connect_db import connect
from sqlmodel import Session, select


# Selecionamos todos los elementos de la tabla
def select_all():
    engine = connect()
    with Session(engine) as session:
        query = select(Proveedor)
        return session.exec(query).all() #Nos devuelve una lista con todos los registros de la tabla
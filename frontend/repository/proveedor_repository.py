from ..model.proveedor_model import Provedor
from .connect_db import conectar_SQLite
from sqlmodel import Session, select, SQLModel, create_engine




def select_all():
    engine = conectar_SQLite()
    with Session(engine) as session:
        query = select(Provedor)
        return session.exec(query).all() #Nos devuelve una lista con todos los registros de la tabla
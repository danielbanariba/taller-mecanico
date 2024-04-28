from ..model.iventario_model import Inventario
from .connect_db import connect
from sqlmodel import Session, select

def select_all():
    engine = connect()
    with Session(engine) as session:
        query = select(Inventario)
        return session.exec(query).all()

def select_inventario_by_id(id_inventario):
    engine = connect()
    with Session(engine) as session:
        query = select(Inventario).where(Inventario.id_inventario == id_inventario)
        return session.exec(query).all()

def create_inventario(inventario: Inventario):
    engine = connect()
    with Session(engine) as session:
        session.add(inventario)
        session.commit()
        query = select(Inventario)
        return session.exec(query).all()

def delete_inventario(id_inventario: int):
    engine = connect()
    with Session(engine) as session:
        query = select(Inventario).where(Inventario.id_inventario == id_inventario)
        inventario_delete = session.exec(query).one()
        session.delete(inventario_delete)
        session.commit()
        query = select(Inventario)
        return session.exec(query).all()

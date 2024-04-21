from ..model.user_model import User
from .connect_db import connect
from sqlmodel import Session, select


# Selecionamos todos los elementos de la tabla
def select_all():
    engine = connect()
    with Session(engine) as session:
        query = select(User)
        return session.exec(query).all() #Nos devuelve una lista con todos los registros de la tabla
    

# Se convierte en un buscardor de usuario por email    
def select_user_by_email(email):
    engine = connect()
    with Session(engine) as session:
        # Esto lo que esta haciendo por debajo es un select * from user where username = email
        query = select(User).where(User.username == email)
        return session.exec(query).all() 
    
# crea usuarios nuevos en la base de datos
def create_user(user: User):
    engine = connect()
    with Session(engine) as session:
        session.add(user)
        session.commit()
        query = select(User)
        return session.exec(query).all()
    
# Elimina un usuario de la base de datos
def delete_user(email: str):
    engine = connect()
    with Session(engine) as session:
        query = select(User).where(User.username == email)
        user_delete = session.exec(query).one()
        session.delete(user_delete)
        session.commit()
        query = select(User)
        return session.exec(query).all() 
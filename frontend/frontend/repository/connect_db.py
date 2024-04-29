from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

#pip install cx_oracle
def connect():
    username = 'C##TALLER_MEC'
    password = 'root1234'
    dns = 'localhost:1521/xe'
    engine = create_engine(f'oracle+cx_oracle://{username}:{password}@{dns}')

    try:
        with engine.connect() as connection:
            print("Conexión exitosa!")
    except SQLAlchemyError as e:
        print("Error al conectar a la base de datos:", str(e))
        return None

    return engine

# if __name__ == "__main__":
#     connect()
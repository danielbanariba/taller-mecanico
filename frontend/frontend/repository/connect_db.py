from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

#pip install cx_oracle
def connect():
    username = 'C##TALLER_MECANICO'
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

if __name__ == "__main__":
    connect()



# def conectar_a_oracle():

#     # Configuración de la conexión Oracle
#     config = {
#         'user': 'C##SOUNDCLOUD11',
#         'password': 'root1234',
#         'dsn': 'localhost:1521/xe',
#         'encoding': 'UTF-8'
#     }

# #Tenemos que poner un try Exception, para evitar cualquier error que pueda ocurrir en la base de datos
#     try:
#         connection = cx_Oracle.connect(**config)
#         print(f"Conectado a Oracle Database {connection.version}")
#         return config  # Devolver el diccionario de configuración
#     except cx_Oracle.Error as err:
#         print("Error de conexión a Oracle:", err)
#         return None

# if __name__ == "__main__":
#     conectar_a_oracle()
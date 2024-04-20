import reflex as rx
from sqlalchemy import create_engine, text

def conectar_SQLite():

    # Configuración de la base de datos
    config = rx.Config(
        app_name="TALLER_MECANICO",
        
        #Base de datos que tenemos en la nube
        db_url= "sqlite:///reflex.db",
        
        #Base de datos que tenemos de manera local
        #db_url="sqlite:///C:\\Users\\banar\\Desktop\\Taller_Mecanico\\backend\\sql\\BD_TALLER_MECANICO.sql", #Esto varia de direccion
        #TODO poner la direccion de la base de datos dependiendo de la computadora en lo que se este trabajando
    )

    # Crear el engine
    engine = create_engine(config.db_url)

    # atrapar la excepción si no se puede conectar a la base de datos
    try:
        conn = engine.connect()
        print("Conexión exitosa a la base de datos.")
        return conn, config #Retornamos la conexión y la configuración
    except Exception as e:
        print("Error al conectar a la base de datos:", e)

if __name__ == "__main__":
    conn, config = conectar_SQLite()
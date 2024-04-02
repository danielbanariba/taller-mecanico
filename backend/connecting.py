import reflex as rx
from sqlalchemy import create_engine, text

config = rx.Config(
    app_name="TALLER_MECANICO",
    #Base de datos que tenemos en la nube
    #db_url= "sqlite:///reflex.db",
    #Base de datos que tenemos de manera local
    db_url="sqlite:///C:\\Users\\banar\\Desktop\\taller-mecanico\\db\\TALLER_MECANICO.db", 
)

# Crear un motor de base de datos
engine = create_engine(config.db_url)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Conexión exitosa a la base de datos.")
except Exception as e:
    print("Error al conectar a la base de datos:", e)
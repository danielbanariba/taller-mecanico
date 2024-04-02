import reflex as rx
from sqlalchemy import create_engine, text

config = rx.Config(
    app_name="TALLER_MECANICO",
    db_url="sqlite:///reflex.db",
)

# Crear un motor de base de datos
engine = create_engine(config.db_url)

try:
    # Intentar ejecutar una consulta simple
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Conexión exitosa a la base de datos.")
except Exception as e:
    print("Error al conectar a la base de datos:", e)
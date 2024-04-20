from sqlalchemy import create_engine, text
from client import conectar_SQLite

# Crea un motor SQLAlchemy
engine = create_engine(conectar_SQLite().db_url)
connection = engine.connect()

# Define tus scripts SQL
sql_script_cliente_natural = """
INSERT INTO CLIENTE_NATURAL (ID_CLIENTE, ID_PERSONA, ID_TIPO)
VALUES
    (1, 1, 1),
    (2, 2, 1),
    (3, 3, 1);
"""

sql_script_empleados = """
INSERT INTO EMPLEADOS (ID_EMPLEADO, ID_CARGO, ID_PERSONA, ID_ESTADO_CIVIL, ID_CONTACTO_EMER, ADJ_DOC, SALARIO)
VALUES
    (1, 1, 4, 1, 1, 'documento_adjunto_empleado_1', 3000.00),
    (2, 2, 5, 1, 2, 'documento_adjunto_empleado_2', 2500.00),
    (3, 3, 6, 1, 3, 'documento_adjunto_empleado_3', 2800.00);
"""

sql_script_proveedor = """
INSERT INTO PROVEEDOR (ID_PROVEEDOR, NOM_PROVEEDOR, ID_DIRECCION, RTN, ID_TEL, CORREO, ID_VENDEDOR, ADJ_DOC)
VALUES
    (1, 'Proveedor 1', 1, 'RTN123', 1, 'proveedor1@example.com', 1, 'documento_adjunto_proveedor_1'),
    (2, 'Proveedor 2', 2, 'RTN456', 2, 'proveedor2@example.com', 2, 'documento_adjunto_proveedor_2'),
    (3, 'Proveedor 3', 3, 'RTN789', 3, 'proveedor3@example.com', 3, 'documento_adjunto_proveedor_3');
"""

# Ejecuta los scripts
connection.execute(text(sql_script_cliente_natural))
connection.execute(text(sql_script_empleados))
connection.execute(text(sql_script_proveedor))

# Cierra la conexión
connection.close()
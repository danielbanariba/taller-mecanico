# Conexión Oracle: 1521
# MySQL: 3306
# pip install cx_Oracle
import cx_Oracle

def conectar_a_oracle():
    
    # Configuración de la conexión Oracle
    config = {
        'user': 'C##TALLER_MECANICO',
        'password': 'root1234',
        'dsn': 'localhost:1521/xe',
        'encoding': 'UTF-8'
    }
    
    #Evita cualquier error que pueda ocurrir en la base de datos
    try:
        connection = cx_Oracle.connect(**config)
        print(f"Conectado a Oracle Database {connection.version}")
        return config  # Devolver el diccionario de configuración
    except cx_Oracle.Error as err:
        print("Error de conexión a Oracle:", err)
        return None
    
if __name__ == "__main__":
    conectar_a_oracle()
    
# Nohelia Hernandez     - 
# Talia Rodriguez       - secia.salvador@unah.hn
# Shery Danelly Cerrato - sherry.cerrato@unah.hn
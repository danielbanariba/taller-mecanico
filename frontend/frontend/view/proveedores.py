from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.components.botones import boton_tres
from frontend.view.modificar_proveedor import detalles_proveedor

# Datos de proveedores como lista de diccionarios
datos_proveedores = [
    {
        "ID": 1,
        "Nombre proveedor": "Proveedor Adgydgsdgucguhcuigsudgcuisdgu",
        "DNI": "12345678901234",
        "RTN": "RTN123",
        "Correo": "proveedora@example.com",
        "Teléfono": "504+0000-1234",
        "Nombre vendedor": "Vendedor A",
        "Teléfono vendedor": "504+0000-5678",
    },
    {
        "ID": 2,
        "Nombre proveedor": "Proveedor B",
        "DNI": "98765432109876",
        "RTN": "RTN456",
        "Correo": "proveedorb@example.com",
        "Teléfono": "504+0000-4321",
        "Nombre vendedor": "Vendedor B",
        "Teléfono vendedor": "504+0000-8765",
    },
    # Otros proveedores...
]

# Crear un DataFrame a partir de la lista de diccionarios
proveedores_data = pd.DataFrame(datos_proveedores)

# Define la función para crear la tabla de proveedores
def Proveedores():
    # Añadir una columna con botones a cada fila usando boton_tres
    proveedores_data['Acción'] = proveedores_data['ID'].apply(
        lambda x: rx.hstack(  # Usar el componente existente
            boton_tres("plus", "/proveedores/modificar_proveedor", "Modificar proveedor"),
        )
    )

    # Crea la tabla de proveedores
    return rx.data_table(
        data=proveedores_data[
            ["ID", "Nombre proveedor", "DNI", "RTN", "Correo", "Teléfono", "Nombre vendedor", "Teléfono vendedor", "Acción"]
        ],
        pagination=True,
        search=True,
        sort=True,
    )

# Define la página que contiene la tabla
def proveedores_page():
    return rx.container(
        Proveedores(),
    )



#CODIGO ANTIGUO

"""# Obtén el directorio del script actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construye la ruta al archivo csv de proveedores
csv_file = os.path.join(current_dir, '../../../backend/db/Proveedores.csv')

# lee el archivo csv y lo guarda en la variable proveedores_data
proveedores_data = pd.read_csv(csv_file)"""

"""def Proveedores():
    # Cambia el nombre de las columnas según sea necesario
    proveedores_data.rename(columns={
        'id': 'ID', 
        'nombre_proveedor': 'Nombre proveedor', 
        'dni': 'DNI', 
        'rtn': 'RTN', 
        'correo': 'Correo', 
        'telefono': 'Telefono', 
        'nombre_vendedor': 'Nombre vendedor', 
        'telefono_vendedor': 'Telefono vendedor',
        '---': '---'
        }, inplace=True)



    #Crea la tabla de proveedores
    return rx.data_table(
        data = proveedores_data[[
            'ID', 
            'Nombre proveedor', 
            'DNI', 
            'RTN', 
            'Correo', 
            'Telefono', 
            'Nombre vendedor', 
            'Telefono vendedor',
        
        ]],
        pagination= True,
        search= True,
        sort= True,
    )

def proveedores_page():
    return rx.container(
        Proveedores(),
    )"""



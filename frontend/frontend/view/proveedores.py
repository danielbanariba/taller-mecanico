from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH

import os

# Obtén el directorio del script actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construye la ruta al archivo csv de proveedores
csv_file = os.path.join(current_dir, '../../../backend/db/Proveedores.csv')

# lee el archivo csv y lo guarda en la variable proveedores_data
proveedores_data = pd.read_csv(csv_file)


def Proveedores():
    # Cambia el nombre de las columnas según sea necesario
    proveedores_data.rename(columns={
        'id': 'ID', 
        'nombre_proveedor': 'Nombre proveedor', 
        'dni': 'DNI', 
        'rtn': 'RTN', 
        'correo': 'Correo', 
        'telefono': 'Telefono', 
        'nombre_vendedor': 'Nombre vendedor', 
        'telefono_vendedor': 'Telefono vendedor'
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
            'Telefono vendedor'
        ]],
        pagination= True,
        search= True,
        sort= True,
    )

def proveedores_page():
    return rx.container(
        Proveedores(),
    )

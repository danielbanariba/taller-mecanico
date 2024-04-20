from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH

import os

# Obtén el directorio del script actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construye la ruta al a
csv_file = os.path.join(current_dir, '../../../db/Empleados')

# lee el archivo csv y lo guarda en la variable proveedores_data
Empleados_data = pd.read_csv(csv_file)


def Empleados():
    # Cambia el nombre de las columnas según sea necesario
    Empleados_data.rename(columns={
        'id': 'ID', 
        'nombre_empleado': 'Nombre empleado', 
        'dni': 'DNI', 
        'rtn': 'RTN', 
        'correo': 'Correo', 
        'telefono': 'Telefono', 
        'direccion': 'Direccion',
        }, inplace=True)



    #Crea la tabla de empleados
    return rx.data_table(
        data = Empleados_data[[
            'ID', 
            'Nombre proveedor', 
            'DNI', 
            'RTN', 
            'Correo', 
            'Telefono', 
            'Direccion', 
        ]],
        pagination= True,
        search= True,
        sort= True,
    )

def empleados_page():
    return rx.container(
        Empleados(),
    )
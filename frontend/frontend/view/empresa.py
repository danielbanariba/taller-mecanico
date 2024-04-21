from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH

import os

# Obtén el directorio del script actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construye la ruta al a
csv_file = os.path.join(current_dir, '../../../db/Empresa')

# lee el archivo csv y lo guarda en la variable empresas_data
Empresa_data = pd.read_csv(csv_file)


def Empresa():
    # Cambia el nombre de las columnas según sea necesario
    Empresa_data.rename(columns={
        'id': 'ID', 
        'nombre_empresa': 'Nombre Empresa', 
        'dni': 'DNI', 
        'rtn': 'RTN', 
        'correo': 'Correo', 
        'telefono': 'Telefono', 
        'direccion': 'Direccion',
        'nombre_representante': 'Nombre representante',
        'telefono_representante': 'Telefono del Representante',
        'correo_representante': 'Correo del Representante',
        }, inplace=True)



    #Crea la tabla de empresas
    return rx.data_table(
        data = Empresa_data[[
            'ID', 
            'Nombre Empresa', 
            'DNI', 
            'RTN', 
            'Correo', 
            'Telefono', 
            'Direccion',
            'Nombre representante',
            'Telefono del Representante',
            'Correo del Representante',
        ]],
        pagination= True,
        search= True,
        sort= True,
    )

def empresa_page():
    return rx.container(
        Empresa(),
    )


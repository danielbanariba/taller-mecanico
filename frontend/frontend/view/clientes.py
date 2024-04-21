from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH

import os

# Obtén el directorio del script actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construye la ruta al a
csv_file = os.path.join(current_dir, '../../../db/Clientes_Naturales')
csv_file = os.path.join(current_dir, '../../../db/Clientes_Juridicos')

# lee el archivo csv y lo guarda en la variable clientes_data
clientes_naturales_data = pd.read_csv(csv_file)
clientes_juridicos_data = pd.read_csv(csv_file)

def ClientesNaturales():
    # Cambia el nombre de las columnas según sea necesario
    # Supongamos que tienes un DataFrame llamado 'clientes_naturales_data' para los clientes naturales
    clientes_naturales_data.rename(columns={
        'id': 'ID', 
        'nombre': 'Nombre', 
        'dni': 'DNI', 
        'correo': 'Correo', 
        'telefono': 'Telefono', 
        'direccion': 'Direccion',
    }, inplace=True)

    # Crea la tabla de clientes naturales
    return rx.data_table(
        data=clientes_naturales_data[[
            'ID', 
            'Nombre', 
            'DNI', 
            'Correo', 
            'Telefono', 
            'Direccion', 
        ]],
        pagination=True,
        search=True,
        sort=True,
    )

def ClientesJuridicos():
    # Cambia el nombre de las columnas según sea necesario
    # Supongamos que tienes un DataFrame llamado 'clientes_juridicos_data' para los clientes jurídicos
    clientes_juridicos_data.rename(columns={
        'id': 'ID', 
        'nombre_empresa': 'Nombre empresa', 
        'rtn': 'RTN', 
        'correo_empresa': 'Correo empresa', 
        'nombre_contacto': 'Nombre contacto', 
        'telefono_contacto': 'Telefono contacto', 
        'direccion': 'Direccion',
    }, inplace=True)

    # Crea la tabla de clientes jurídicos
    return rx.data_table(
        data=clientes_juridicos_data[[
            'ID', 
            'Nombre empresa', 
            'RTN', 
            'Correo empresa', 
            'Nombre contacto', 
            'Telefono contacto', 
            'Direccion', 
        ]],
        pagination=True,
        search=True,
        sort=True,
    )

def clientes_naturales_page():
    return rx.container(
        ClientesNaturales(),
    )

def clientes_juridicos_page():
    return rx.container(
        ClientesJuridicos(),
    )

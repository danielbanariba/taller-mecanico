from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH

import os

# Obtén el directorio del script actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construye la ruta al a
csv_file = os.path.join(current_dir, '../../../db/Cliente_N')

# lee el archivo csv y lo guarda en la variable empresas_data
Cliente_N_data = pd.read_csv(csv_file)


def Cliente_N():
    # Cambia el nombre de las columnas según sea necesario
    Cliente_N_data.rename(columns={
        'id': 'ID', 
        'nombre_cliente': 'Nombre Cliente', 
        'dni': 'DNI', 
        'rtn': 'RTN', 
        'correo': 'Correo', 
        'telefono': 'Telefono', 
        'direccion': 'Direccion',
        }, inplace=True)



    #Crea la tabla de cliente
    return rx.data_table(
        data = Cliente_N_data[[
            'ID', 
            'Nombre Cliente', 
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

def cliente_n_page():
    return rx.container(
        Cliente_N(),
    )


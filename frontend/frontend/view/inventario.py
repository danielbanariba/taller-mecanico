from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH

import os

# Obtén el directorio del script actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construye la ruta al archivo csv
csv_file = os.path.join(current_dir, '../../../db/Inventory_v2.csv')

nba_data = pd.read_csv(csv_file)


#Una forma para hacer tablas, pero me interesa mas el del archivo csv
# class State(rx.State):
#     data: List = [
#         ["Lionel", "Messi", "PSG"],
#         ["Christiano", "Ronaldo", "Al-Nasir"],
#     ]
#     columns: List[str] = ["First Name", "Last Name"]

# def inventario():
#     return rx.data_table(
#         data=State.data,
#         columns=State.columns,
#         search= True,
#     )


def inventario():
    # Cambia el nombre de la columna 
    nba_data.rename(columns={
        'product.partNumber': 'ID', 
        'class': 'Condicion', 
        'value': 'Precio', 
        'quantity': 'Cantidad', 
        'inventoryType': 'Tipo de Inventario', 
        'reservationOrders': 'Orden de Reservacion',
        'daysOfSupply' : 'Dias de Suministro',
        'shelfLife' : 'Vida Util',
        'expectedLeadTime' : 'Tiempo de Entrega Esperado',
        'segment' : 'Categoria',
        }, inplace=True)
    
    return rx.data_table(
        data = nba_data[[
            'ID',  # Usa el nuevo nombre de la columna aquí
            'Tipo de Inventario',
            'Cantidad', 
            'Precio', 
            'Orden de Reservacion', 
            'Dias de Suministro', 
            'Vida Util', 
            'Tiempo de Entrega Esperado', 
            'Condicion', 
            'Categoria'
        ]],
        pagination= True,
        #TODO agregar un icono de busqueda
        search= True,
        sort= True,
    )
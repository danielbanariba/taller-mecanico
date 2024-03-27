import pandas as pd

import os

# Obtén el directorio del script actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construye la ruta al archivo csv
csv_file = os.path.join(current_dir, '../../../db/Inventory_v2.csv')

# Lee el archivo csv
nba_data = pd.read_csv(csv_file)

# Imprime las columnas del DataFrame
print(nba_data.columns)
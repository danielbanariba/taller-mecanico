#aqui vamos a poner los links o las direcciones de los archivos donde se van a dirigir cada modulo
# https://reflex.dev/docs/library/typography/link/


#--------------------------------------------Ivento mio xd------------------------------
import reflex as rx
from frontend.view.inventario import inventario

app = rx.App()

INVENTARIO2 = app.add_page(inventario, route="/iventario")
#--------------------------------------------Ivento mio xd------------------------------

INVENTARIO = "#Inventario"
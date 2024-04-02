import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inventario import inventario
from frontend.view.inicio import inicio
from frontend.view.inicio_de_sesion import inicio_de_sesion


def index() -> rx.Component:
    return rx.vstack(
        navbar(),
        #inicio_de_sesion(),
        rx.hstack(
            inicio(),
            #inventario(),#TODO: esto solo es una prueba, se debe cambiar por la pagina de inicio    
        ),
    )
app = rx.App()
#--------------------------------------------Ivento mio xd------------------------------
app.add_page(inventario, route="/iventario")
#--------------------------------------------Ivento mio xd------------------------------
app.add_page(index)
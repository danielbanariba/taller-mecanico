import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inventario import inventario
from frontend.view.inicio import inicio


def index() -> rx.Component:
    return rx.vstack(
        navbar(),
        inicio(),
        #inventario(),#TODO: esto solo es una prueba, se debe cambiar por la pagina de inicio
    )


app = rx.App()
app.add_page(index)

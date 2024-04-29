import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inicio import Inicio
from frontend.inventario_page import inventario_page

def inventarios():
    return rx.vstack(
        navbar(),
        rx.hstack(
            Inicio(),
            inventario_page()
        )
    )
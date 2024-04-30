import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inicio import Inicio
from frontend.view.agregar_cotizacion import formulario_cotizacion

#Página de agregar cotización
def agregar_cotizacion_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            formulario_cotizacion(),   
        ),
    )
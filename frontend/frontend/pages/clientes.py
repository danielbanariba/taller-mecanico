import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inicio import Inicio
from frontend.view.agregar_cliente import code_setter

def agregar_cliente_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            code_setter(),   
        ),
    )
    
def clientes_page2():
    return rx.vstack(
        navbar(),
        rx.hstack(
            Inicio(),
            rx.link(
                rx.image(
                    src="/img/cliente/agregar_cliente.png",
                    width="100",
                    height="100",
                ),
                href="/clientes/agregar_cliente",
            ),
        )
    )
    
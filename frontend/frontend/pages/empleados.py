import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inicio import Inicio

def empleado_page():
    return rx.vstack(
        navbar(),
        rx.hstack(
            Inicio(),
            rx.link(
                rx.image(
                    src="/img/empleado/agregar_empleado.png",
                    width="100",
                    height="100",
                ),
                href="/empleados/agregar_empleado",
            ),
        )
    )
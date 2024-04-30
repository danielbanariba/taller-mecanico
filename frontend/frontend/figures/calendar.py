from reflex_calendar import calendar
import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inicio import Inicio

def calendar_page():
    return rx.vstack(  # Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            calendar(),  # Pasa la función como prop
        ),
    )
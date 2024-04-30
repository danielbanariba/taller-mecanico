import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inicio import Inicio
from frontend.view.pantalla_dashboard import grafica_de_barras, grafica_lineal
from frontend.view.pantalla_dashboard import grafica_de_barras, grafica_lineal, grafica_de_barras_comparable, grafica_de_area

#Pagina de estadisticas
def estadisticas():
    return rx.vstack(
        navbar(),
        rx.hstack(
            Inicio(),
                rx.flex(
                    grafica_lineal(),
                    grafica_de_barras(),
                    grafica_de_barras_comparable(),
                    grafica_de_area(),
                    spacing="2",
                    flex_wrap="wrap",
                    width="100%",
                )
            )
        )
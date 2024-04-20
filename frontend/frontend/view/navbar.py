import reflex as rx
from frontend.styles.colors import Color
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.figures.tuercas import tuercas

#Esto es de la parte superiro de la pagina
def navbar() -> rx.Component:
    return rx.hstack(
        rx.image(
            src="/img/logo/logo-5.png", # Logo de la pagina
            width="auto",
            height="80px",
            margin_top=Size.SMALL.value,
            margin_bottom=Size.ZERO.value,
            margin_left=Size.MEDIUM.value,
        ),
        tuercas(),
        bg=Color.NARVAR.value,
        padding_x=Size.BIG.value, # Espacio que hay entre el borde y el texto
        padding_y=Size.VERY_SMALL.value,
        padding_top=Size.VERY_SMALL.value,
        width="100%",
    )
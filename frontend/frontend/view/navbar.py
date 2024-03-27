import reflex as rx
from frontend.styles.colors import Color
from frontend.styles.styles import Size, MAX_WIDTH

def navbar() -> rx.Component:
    return rx.hstack(
        rx.container(
            #TODO: Aqui tiene que ir el logo de la empresa
            rx.box(
                rx.avatar(fallback="RX", size="6"),
                max_width=MAX_WIDTH,
            ),
        ),
        bg=Color.NARVAR.value,
        padding_x=Size.BIG.value, # Espacio que hay entre el borde y el texto
        padding_y=Size.VERY_SMALL.value,
        padding_top=Size.VERY_SMALL.value,
        width="100%",
    )
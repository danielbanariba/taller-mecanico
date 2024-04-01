import reflex as rx
from frontend.styles.colors import Color
from frontend.styles.styles import Size, MAX_WIDTH

def navbar() -> rx.Component:
    return rx.hstack(
        rx.image(
            src="/img/logo/logo-5.png",
            width="auto",
            height="80px",
            margin_top=Size.SMALL.value,
            margin_bottom=Size.ZERO.value,
            margin_left=Size.MEDIUM.value,
        ),
        bg=Color.NARVAR.value,
        padding_x=Size.BIG.value, # Espacio que hay entre el borde y el texto
        padding_y=Size.VERY_SMALL.value,
        padding_top=Size.VERY_SMALL.value,
        width="100%",
    )
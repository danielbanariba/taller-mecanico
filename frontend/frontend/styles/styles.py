from enum import Enum
import reflex as rx
from .colors import TextColor, Color
from .fonts import Font, FontWeight

# Ancho maximo de la pagina web
MAX_WIDTH = "1000px"


class Size(Enum): # Tamanno de las imagenes
    ZERO = "0px !important"
    VERY_SMALL = "0.2em"
    SMALL = "0.5em"
    MEDIUM = "0.8em"
    DEFAULT = "1em"
    PEQUENIO = "1.2em"
    LARGE = "1.5em"
    GRANDELOGO = "1.7em"
    BIG = "1.9em"
    MUY_BIG = "2.5em"
    PLATAFORMAS = "3em"
    VERY_BIG = "4em"
    GIGANTE = "8em"

#Hojas de estilos
STYLESHEETS = [
    "fonts/fonts.css", # Ir al archvivo fonts.py para ver las fuentes
]

BASE_STYLE = {
    "font_family": Font.DEFAULT.value,
    "font_weight": "bold",
    "color": TextColor.PRIMARY.value,
    "background_color": Color.NARVAR.value,
}

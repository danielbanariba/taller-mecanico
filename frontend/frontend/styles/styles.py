from enum import Enum
import reflex as rx
from .colors import TextColor, Color
from .fonts import Font, FontWeight

# Ancho maximo de la pagina web
MAX_WIDTH = "1500px" # "1000px"

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

CENTRAR_LOGIN = {
    "display": "flex",
    "justifyContent": "center",
    "alignItems": "center",
    "height": "100vh",
    "width": "100%",
}

#BOTONES del menú lateral izquierdo (INICIO)
STYLE_BUTTON={
    'width': '400px', 
    'height': '60px',
    'backgroundColor': '#b39eff',
    'cursor': 'pointer',  # Cambia el cursor a una mano
    'margin': '0',
    'fontSize': '20px',  # Ajusta el tamaño del texto aquí
    ':hover': {
        'backgroundColor': '#9f87de',  # Cambia el color de fondo cuando se pasa el cursor por encima
        'transition': '0.3s',
    },
},

#BOTONES para agregar, modificar...
STYLE_BUTTON_TWO={
    'width': '150px', 
    'height': '40px',
    'backgroundColor': '#b39eff',
    'cursor': 'pointer',  # Cambia el cursor a una mano
    'margin': '0',
    'fontSize': '20px',  # Ajusta el tamaño del texto aquí
    ':hover': {
        'backgroundColor': '#9f87de',  # Cambia el color de fondo cuando se pasa el cursor por encima
        'transition': '0.3s',
    },
},

style_notify = {
    'position': 'fixed',
    'top': '0',
    'right': '0',
    'margin': '10px 10px',
}
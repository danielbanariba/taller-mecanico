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

CENTRAR_INICIO_DE_SESION = {
    "display": "flex",
    "justifyContent": "center",
    "alignItems": "center",
    "height": "100vh",
    "width": "100%",
}

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

#TODO chacar esto para que de el estilo que esta en el figma si no, cambiarlo por otro
def fondo_bg_inicio_seccion():
    return rx.html(
    """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            section {
                position: relative;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 400px;
                padding-top: 100px;
                background: #3c31dd;
            }

            .curve {
                position: absolute;
                height: 250px;
                width: 100%;
                bottom: 0;
                text-align: center;
            }

            .curve::before {
                content: '';
                display: block;
                position: absolute;
                border-radius: 100% 50%;
                width: 55%;
                height: 100%;
                transform: translate(85%, 60%);
                background-color: hsl(216, 21%, 16%);
            }

            .curve::after {
                content: '';
                display: block;
                position: absolute;
                border-radius: 100% 50%;
                width: 55%;
                height: 100%;
                background-color: #3c31dd;
                transform: translate(-4%, 40%);
                z-index: -1;
            }
        </style>
    </head>
    <body>
        <section>
        <!-- content here -->
        <div class="curve"></div>
        </section>
    </body>
    </html>
    
    """
    )

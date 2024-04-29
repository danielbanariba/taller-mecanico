import reflex as rx
import frontend.styles.colors as colors
from frontend.styles.styles import STYLE_BUTTON
from frontend.styles.styles import STYLE_BUTTON_TWO

def boton(icon: str, url: str, name: str):
    return rx.box(
        rx.link(
            rx.button(
            rx.icon(tag=icon),#va a recibir el icono correspondiente del directorio de la pagina, https://lucide.dev/icons/
            name,
            style={
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
            ),
            href=url,#va a recibir el link correspondiente del directorio de la pagina
        )
    )

#BOTONES (medianos) de agregar, modificar... usar esta función para llamar los estilos
def boton_dos (icon: str, url: str, name: str):
    return rx.box(
        rx.link(
            rx.button(
            rx.icon(tag=icon),#va a recibir el icono correspondiente del directorio de la pagina, https://lucide.dev/icons/
            name,
            style={
                'width': '200px', 
                'height': '40px',
                'backgroundColor': '#b39eff',
                'cursor': 'pointer',  # Cambia el cursor a una mano
                'margin': '0',
                'fontSize': '15px',  # Ajusta el tamaño del texto aquí
                ':hover': {
                    'backgroundColor': '#9f87de',  # Cambia el color de fondo cuando se pasa el cursor por encima
                    'transition': '0.3s',
                    },
                },
            ),
            href=url,#va a recibir el link correspondiente del directorio de la pagina
        )
    )

#BOTONES (pequeños) de guardar, cancelar... usar esta función para llamar los estilos
def boton_tres (icon: str, url: str, name: str):
    return rx.box(
        rx.link(
            rx.button(
            rx.icon(tag=icon),#va a recibir el icono correspondiente del directorio de la pagina, https://lucide.dev/icons/
            name,
            style={
                'width': '150px', 
                'height': '30px',
                'backgroundColor': '#b39eff',
                'cursor': 'pointer',  # Cambia el cursor a una mano
                'margin': '0',
                'fontSize': '9px',  # Ajusta el tamaño del texto aquí
                ':hover': {
                    'backgroundColor': '#9f87de',  # Cambia el color de fondo cuando se pasa el cursor por encima
                    'transition': '0.3s',
                    },
                },
            ),
            href=url,#va a recibir el link correspondiente del directorio de la pagina
        )
    )
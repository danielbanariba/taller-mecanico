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

#BOTONES de agregar, modificar... usar esta función para llamar los estilos
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
def boton_clientes(icon1: str, url1: str, name1: str, icon2: str, url2: str, name2: str):
    return rx.div(
        rx.link(
            rx.button(
                rx.icon(tag=icon1),
                name1,
                style={
                    'width': '200px',
                    'height': '40px',
                    'backgroundColor': '#b39eff',
                    'cursor': 'pointer',
                    'margin': '0',
                    'fontSize': '15px',
                    ':hover': {
                        'backgroundColor': '#9f87de',
                        'transition': '0.3s',
                    },
                },
            ),
            href=url1,
        ),
        rx.link(
            rx.button(
                rx.icon(tag=icon2),
                name2,
                style={
                    'width': '200px',
                    'height': '40px',
                    'backgroundColor': '#b39eff',
                    'cursor': 'pointer',
                    'margin': '0',
                    'fontSize': '15px',
                    ':hover': {
                        'backgroundColor': '#9f87de',
                        'transition': '0.3s',
                    },
                },
            ),
            href=url2,
        ),
        style={'display': 'flex', 'gap': '10px'}  # Alinea los botones en una fila
    )

# Ejemplo de uso:
# boton_dos(icon1='user', url1='/clientes-naturales', name1='Clientes Naturales', icon2='building', url2='/clientes-juridicos', name2='Clientes Jurídicos')

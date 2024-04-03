import reflex as rx
import frontend.styles.colors as colors

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
                },
                },
            ),
            href=url,#va a recibir el link correspondiente del directorio de la pagina
        )
    )
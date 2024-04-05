import reflex as rx
from frontend.styles.styles import CENTRAR_INICIO_DE_SESION
from frontend.styles.styles import fondo_bg_inicio_seccion

# para mas informacion de como hacer la pagina de inicio de sesion
# https://reflex.dev/docs/library/forms/form/

# para poder hacer el diseño de la pagina de inicio de sesion
# https://fireship.io/lessons/wavy-backgrounds/
# https://plantillashtmlgratis.com/categoria/efectos-css/fondos-animados-css/

class FormState(rx.State):
    form_data: dict = {}

    def handle_submit(self, form_data: dict):
        """Handle the form submit."""
        self.form_data = form_data

def inicio_de_sesion():
    return rx.box(
        rx.card(
            rx.vstack(
                rx.text("Inicio de sesión", size="3", align="center"),  # Añade un tamaño de texto de 2
                rx.form(
                    rx.vstack(
                        rx.text("Inicio de sesión", size="3"),  # Añade un tamaño de texto de 2
                        rx.input(
                            placeholder="Correo Electronico",
                            name="email",
                            style={"width": "30em", "height": "4em"}  # Añade un estilo de ancho y altura al elemento de entrada
                        ),
                        rx.text("Contraseña", size="3"),  # Añade un tamaño de texto de 1
                        rx.input(
                            placeholder="Contraseña",
                            name="password",
                            type="password",
                            style={"width": "30em", "height": "4em"}  # Añade un estilo de ancho y altura al elemento de entrada
                        ),
                        rx.hstack(
                            rx.checkbox("Checked", name="check"),
                            rx.switch("Switched", name="switch"),
                        ),
                        rx.button(
                            "Iniciar sesión",
                            type="submit",
                            width= "20em",
                            height= "4em",
                        ),  # Añade un estilo de ancho y altura al botón
                    ),
                    on_submit=FormState.handle_submit,
                    reset_on_submit=True,
                ),
                #TODO aqui es donde se lo tendremos que ensennar al ingeniero, para que mire que los datos fluyen de manera incriptada
                # descomentar para que se pueda ver
                # rx.divider(),
                # rx.heading("Lo que se manda a la base de datos"),
                # rx.text(FormState.form_data.to_string()),
            ),
            #Estilo de los bordes del incio de seccion
            #TODO pero este fragmento de codigo se tiene que llevar al archivo de estilos 
            border = "10px solid rebeccapurple",
            border_radius = "1em",
            # Añade un estilo de ancho y altura a la tarjeta
            #style={"width": "800px", "height": "600px"}
        ),
        style=CENTRAR_INICIO_DE_SESION
    )
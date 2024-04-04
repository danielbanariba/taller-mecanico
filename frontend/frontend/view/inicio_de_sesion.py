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
                rx.form(
                    rx.vstack(
                        rx.input(
                            placeholder="Correo Electronico",
                            name="email",
                        ),
                        rx.input(
                            placeholder="Contraseña",
                            name="password",
                            type="password",
                        ),
                        rx.hstack(
                            rx.checkbox("Checked", name="check"),
                            rx.switch("Switched", name="switch"),
                        ),
                        rx.button("Submit", type="submit"),
                    ),
                    on_submit=FormState.handle_submit,
                    reset_on_submit=True,
                ),
                rx.divider(),
                rx.heading("Results"),
                rx.text(FormState.form_data.to_string()),
            ),
            #Estilo de los bordes del incio de seccion
            #TODO pero este fragmento de codigo se tiene que llevar al archivo de estilos 
            border = "10px solid rebeccapurple",
            border_radius = "1em",
            border_top_right_radius = "10% 30%",
        ),
        style=CENTRAR_INICIO_DE_SESION
    )
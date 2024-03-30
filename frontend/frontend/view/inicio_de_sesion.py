import reflex as rx
from frontend.styles.styles import CENTRAR_INICIO_DE_SESION

# para mas informacion de como hacer la pagina de inicio de sesion
# https://reflex.dev/docs/library/forms/form/

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
        ),
        style=CENTRAR_INICIO_DE_SESION
    )
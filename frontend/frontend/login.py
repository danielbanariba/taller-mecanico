import reflex as rx
import requests as rq
import re
from frontend.components.form_password import form_password
from frontend.components.form_user import form_user

class LoginState(rx.State):
    loader: bool = False
    username: str = "exampl@mail.com"
    password: str
    error = False
    response: dict = {}
    
    @rx.background
    async def loginService(self, data: dict):
        async with self:
            self.loader = True
            self.error = False
            # Cambia la URL del endpoint de login en loginService
            response = rq.post('http://localhost:8000/login/', json=data, headers={'Content-Type': 'application/json'})     
            if response.status_code == 200:
                self.response = response.json()
                self.loader = False
                #Cuando se inicia seccion lo redirige a la pagina de estadisticas
                return rx.redirect('/estadisticas') 
            else:
                self.loader = False
                self.error = True

    @rx.var
    def user_invalid(self)->bool:
        return not (re.match(r"[^@]+@[^@]+.[^@]+", self.username) and "example@mail.com")

    @rx.var
    def user_empty(self)->bool:
        return not self.username.strip()
    
    @rx.var
    def password_empty(self)->bool:
        return not (self.password.strip())

    @rx.var
    def validate_fields(self) -> bool:
        return (
            self.user_empty 
            or self.user_invalid 
            or self.password_empty
        )


#@rx.route('/login', title='Login')
def Login() -> rx.Component:
    return rx.section(
        rx.flex(
            rx.image(src='/login.png', width="300px", border_radius="15px 50px"),
            rx.heading('Inicio de sesion'),
            rx.form.root(
                rx.flex(
                    form_user("Usuario", "Ingrese su correo", "Ingrese un correo valido", "username", LoginState.set_username, LoginState.user_invalid),
                    
                    form_password("Contraseña", "Ingrese su contraseña", "password", LoginState.set_password, "password"),
                    
                    rx.form.submit(
                            rx.cond(
                                LoginState.loader,
                                rx.chakra.spinner(color="red", size="xs"),
                                rx.button(
                                    "Iniciar sesion",
                                    disabled=LoginState.validate_fields,
                                    width="30vw",
                                ),     
                            ),
                            as_child=True,
                        ),
                        direction="column",
                        justify="center",
                        align="center",
                        spacing="2",
                ),
                    rx.cond(
                        LoginState.error,
                        rx.callout(
                            "Credenciasles Incorrectas",
                            icon="alert_triangle",
                            color_scheme="red",
                            role="alert",
                            style={"margin-top": "10px"}
                        ),
                    ),
                    on_submit=LoginState.loginService,
                    reset_on_submit=True,
                    width="80%",
                ),
                width="100%",
                direction="column",
                align="center",
                justify="center",
            ),
            style=style_section,
            justify="center",
            width="100%",
        )
    
style_section = {
    "height": "90vh",
    "width": "80%",
    "margin": "auto",
}
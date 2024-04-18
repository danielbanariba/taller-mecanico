import reflex as rx
import requests as rq
import re
    
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
import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inicio import Inicio
from frontend.user_page import user_page, UserState

#Página de inicio
def usuarios():
    return rx.vstack(
        navbar(),
        rx.hstack(
            Inicio(),
            user_page()
        )
    )
    

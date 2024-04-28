import reflex as rx
from user_page import user_page

def clientes_page():
    return rx.box(
        user_page(),
    )
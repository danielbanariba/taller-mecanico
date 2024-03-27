import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inventario import inventario


def index() -> rx.Component:
    return rx.vstack(
        navbar(),
        inventario(),
    )


app = rx.App()
app.add_page(index)

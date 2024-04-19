import reflex as rx
from frontend.view.navbar import navbar

def error_404() -> rx.Component:
    return rx.vstack(
        #navbar(),
        rx.box(
                rx.vstack(
                    rx.center(
                        rx.text("Oops! Page not found"),
                    ),                    
                    rx.image(# TODO: poner una una llanata punchada a la par de 404
                        src="/404/404.jpg",
                    ),
                ),
            display= "flex",
            justifyContent = "center",
            alignItems= "center",
            height= "100vh",
            width= "100%",
            bg= "#ffd83b"
        )
    )
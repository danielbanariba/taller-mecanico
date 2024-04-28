import reflex as rx

def perfil(photo: str, name: str, email: str) -> rx.Component:
    return rx.box(
        rx.dialog.root(
            rx.dialog.trigger(
                rx.avatar(
                    src=photo, 
                    size="7"), 
                ),
            rx.dialog.content(
                rx.dialog.title("Editar Perfil"),
                rx.dialog.description(
                    "Change your profile details and preferences.",
                    size="2",
                    margin_bottom="16px",
                ),
                rx.flex(
                    rx.text(
                        "Nombre",
                        as_="div",
                        size="2",
                        margin_bottom="4px",
                        weight="bold",
                    ),
                    rx.input(
                        default_value=name,
                        placeholder="Ingrese su nombre",
                    ),
                    rx.text(
                        "Correo Electrónico",
                        as_="div",
                        size="2",
                        margin_bottom="4px",
                        weight="bold",
                    ),
                    rx.input(
                        default_value=email,
                        placeholder="Ingrese su correo electrónico",
                    ),
                    direction="column",
                    spacing="3",
                ),
                rx.flex(
                    rx.dialog.close(
                        rx.button(
                            "Cancelar",
                            color_scheme="gray",
                            variant="soft",
                        ),
                    ),
                    rx.dialog.close(
                        rx.button("Guardar"),
                    ),
                    spacing="3",
                    margin_top="16px",
                    justify="end",
                ),
            ),
        ),
    position = "fixed",
    right = "10px",
    top = "2%",
)


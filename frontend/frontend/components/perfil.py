import reflex as rx

def perfil(photo: str, naturaleza_cliente: str, name: str, email: str, direccion: str,  dni: str, telefono: str, rtn: str) -> rx.Component:
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
                    "Puedes editar tu perfil en cualquier momento, solo asegurate de que la información sea correcta.",
                    size="2",
                    margin_bottom="16px",
                ),
                rx.flex(
                    rx.text(
                        "Naturalza del Cliente",
                        as_="div",
                        size="2",
                        margin_bottom="4px",
                        weight="bold",
                    ),
                    rx.input(
                        default_value=naturaleza_cliente,
                        placeholder="Ingrese la naturaleza del cliente",
                    ),
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
                    rx.text(
                        "Direccion",
                        as_="div",
                        size="2",
                        margin_bottom="4px",
                        weight="bold",
                    ),
                    rx.input(
                        default_value=direccion,
                        placeholder="Ingrese la dirección",
                    ),
                    rx.text(
                        "DNI",
                        as_="div",
                        size="2",
                        margin_bottom="4px",
                        weight="bold",
                    ),
                    rx.input(
                        default_value=dni,
                        placeholder="Ingrese el DNI",
                    ),
                    rx.text(
                        "Telefono",
                        as_="div",
                        size="2",
                        margin_bottom="4px",
                        weight="bold",
                    ),
                    rx.input(
                        default_value=telefono,
                        placeholder="Ingrese el numero de telefono",
                    ),
                    rx.text(
                        "RTN",
                        as_="div",
                        size="2",
                        margin_bottom="4px",
                        weight="bold",
                    ),
                    rx.input(
                        default_value=rtn,
                        placeholder="Ingrese el RTN",
                    ),
                direction="column",
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


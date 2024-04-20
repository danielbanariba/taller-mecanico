from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.components.botones import boton_tres


import os

def detalles_proveedor():
    return rx.vstack(
        rx.form.root(
            rx.flex(
                *[
                    rx.flex(
                        rx.image(
                            src="/taller-mecanico/frontend/assets/img/user/user-1.png", #se agrega la imagen del usuario
                            width="200px",  # Ancho de la imagen
                            high="200px",
                            margin_right="10px",  # Margen derecho para separarla del badge
                        ),
                        rx.badge(
                            "Activo",
                            color_scheme="grass",
                            variant="solid",
                            high_contrast=False,
                        ),
                        direction="row",
                        justify="between",
                        align="center",  # Alinea verticalmente la imagen y el badge
                    )
                    for cookie_type in ["Estado  "]
                ],
                direction="column",
                spacing="3",
            ),
            width="100%",
        ),
        rx.divider(),
        rx.table.root(
            rx.table.header(rx.table.row(rx.table.column_header_cell("Details"))),
            rx.table.body(
                rx.table.row(
                    rx.table.row_header_cell("Nombre del proveedor"),
                    rx.table.cell("Auto repuestos"),
                ),
                rx.table.row(
                    rx.table.row_header_cell("RTN"),
                    rx.table.cell("0809-1990-001893"),
                ),
                rx.table.row(
                    rx.table.row_header_cell("Dirección"),
                    rx.table.cell("San Pedro Sula, Bo. Cabañas"),
                ),
                rx.table.row(
                    rx.table.row_header_cell("Télefono proveedor"),
                    rx.table.cell("3837-4019/2201-2011"),
                ),
                rx.table.row(
                    rx.table.row_header_cell("Correo proveedor"),
                    rx.table.cell("autorepuestos20@gmail.com"),
                ),
                rx.table.row(
                    rx.table.row_header_cell("Nombre vendedor"),
                    rx.table.cell("José Danilo Carranza Rodriguez"),
                ),
                rx.table.row(
                    rx.table.row_header_cell("DNI"),
                    rx.table.cell("0305-1984-02315"),
                ),
                rx.table.row(
                    rx.table.row_header_cell("Télefono vendedor"),
                    rx.table.cell("9952-1244"),
                ),
                rx.table.row(
                    rx.table.row_header_cell("Correo vendedor"),
                    rx.table.cell("jdanilo@yahoo.com"),
                ),
            ),
        ),
        rx.hstack(
            boton_tres("star", "/alert", "Modificar"),
            boton_tres("x", "/alert", "Cancelar"),
        ),
        width="100%",
    )


def modificar_proveedores_page():
    return rx.container(
        detalles_proveedor(),
    )


































"""class FormSwitchState2(rx.State):
    form_data: dict = {}

    cookie_types: dict[str, bool] = {}

    def handle_submit(self, form_data: dict):
        
        self.form_data = form_data

    def update_cookies(
        self, cookie_type: str, enabled: bool
    ):
        self.cookie_types[cookie_type] = enabled


def detalles_proveedor():
    return rx.vstack(
        rx.form.root(
            rx.flex(
                *[
                    rx.flex(
                        rx.image(
                            src="ruta/a/la/imagen.png",
                            width="200px",  # Ancho de la imagen
                            margin_right="10px",  # Margen derecho para separarla del switch
                        ),
                        rx.text(
                            rx.flex(
                                rx.cond(
                                    FormSwitchState2.cookie_types[
                                        cookie_type
                                    ],
                                    "Activo",
                                    "Inactivo",
                                ),
                                rx.switch(
                                    name=cookie_type,
                                    checked=FormSwitchState2.cookie_types[
                                        cookie_type
                                    ],
                                    on_change=lambda checked: FormSwitchState2.update_cookies(
                                        cookie_type,
                                        checked,
                                    ),
                                ),
                                spacing="2",
                            ),
                            as_="div",
                            size="2",
                            margin_bottom="4px",
                            weight="bold",
                        ),
                        direction="row",
                        justify="between",
                        align="center",  # Alinea verticalmente la imagen y el texto
                    )
                    for cookie_type in [
                        "Estado  ",
                    ]
                ],
                direction="column",
                spacing="3",
            ),
            on_submit=FormSwitchState2.handle_submit,
            reset_on_submit=True,
            width="100%",
        ),
        rx.divider(),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Details")
                )
            ),
            rx.table.body(
                rx.table.row(
                    rx.table.row_header_cell("Full name"),
                    rx.table.cell("Danilo Sousa\ndanilo@example.com\nDeveloper")
                ),
                rx.table.row(
                    rx.table.row_header_cell("Full name"),
                    rx.table.cell("Dirección\Col.Arturo Quezada")
                ),
                rx.table.row(
                    rx.table.row_header_cell("Full name"),
                    rx.table.cell("Vendedor\Jose Jimenez")
                )
            ),
        ),
        rx.hstack(
            boton_tres("save", "/alert", "Guardar"),
            boton_tres("x", "/alert", "Cancelar"),
        ),
        width="100%",
    )

def modificar_proveedores_page():
    return rx.container(
        detalles_proveedor(),
    )"""



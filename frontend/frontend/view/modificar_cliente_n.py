from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.components.botones import boton_tres


import os

def detalles_clientes_n():
    return rx.vstack(
        rx.form.root(
            rx.flex(
                *[
                    rx.flex(
                        rx.image(
                            src="frontend/assets/img/user/user-1.png",
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
                    rx.table.row_header_cell("ID de Clinte "),
                  rx.table.cell("453"),
                ),

                rx.table.row(
                    rx.table.row_header_cell("Nombre del cliente"),
                    rx.table.cell("Julian Sorto"),
                ),

                rx.table.row(
                    rx.table.row_header_cell("Empresa"),
                    rx.table.cell(" "),
                ),

                rx.table.row(
                    rx.table.row_header_cell("Naturaleza Cliente"),
                    rx.table.cell("Juridico"),
                ),
                 rx.table.row(
                    rx.table.row_header_cell("RTN"),
                    rx.table.cell("0809-1990-000189"),
                ),
                
                rx.table.row(
                    rx.table.row_header_cell("Télefono"),
                    rx.table.cell("3837-4019/2201-2011"),
                ),
                
            ),
        ),
        rx.hstack(
            boton_tres("star", "/alert", "Modificar"),
            boton_tres("x", "/alert", "Cancelar"),
        ),
        width="100%",
    )


def modificar_cliente_n_page():
    return rx.container(
        detalles_clientes_n(),
    )

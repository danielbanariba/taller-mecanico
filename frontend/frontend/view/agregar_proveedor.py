# agregar_proveedor_page.py
from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.components.botones import boton_dos
from frontend.components.botones import boton_tres
from frontend.view.modificar_proveedor import detalles_proveedor

def formulario_agregar_proveedor():
    return rx.container(
        rx.text("Agregar Proveedor", size="3", margin_bottom="35px"),  # Título del formulario

        # Subir documentación y Seleccionar departamento en la misma fila
        rx.hstack(
            boton_dos("plus", "/proveedores/agregar_proveedor/subir_doc", "Agregar documento"),
            rx.select(
                [
                    "Atlántida", #Estos datos seran estraídos de la base de datos
                    "Choluteca",
                    "Colón",
                    "Comayagua",
                    "Copán",
                    "Cortés",
                    "El Paraíso",
                    "Francisco Morazán", #Estos datos seran estraídos de la base de datos
                    "Gracias a Dios",
                    "Intibucá",
                    "Islas de la Bahía",
                    "La Paz",
                    "Lempira",
                    "Ocotepeque",
                    "Olancho",
                    "Santa Bárbara",
                    "Valle",
                    "Yoro",
                ],
                name="departamento",
                placeholder="Selecciona un departamento",
                margin_bottom="35px",
                style={"width": "400px"}
            ),
        ),

        # Campos de entrada para los proveedores
        rx.vstack(
            # Dirección
            rx.vstack(
                rx.text("Dirección", margin_bottom="5px"),
                rx.input(
                    type="text",
                    placeholder="Dirección",
                    name="direccion",
                    multiline=True,
                    rows=3,
                    margin_bottom="20px",
                    style={"width": "400px"}
                ),
            ),

            # Nombre del proveedor y RTN
            rx.hstack(
                rx.vstack(
                    rx.text("Nombre del proveedor", margin_bottom="5px"),
                    rx.input(
                        type="text",
                        placeholder="Nombre del proveedor",
                        name="nombre_proveedor",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
                rx.vstack(
                    rx.text("RTN", margin_bottom="5px"),
                    rx.input(
                        type="number",
                        placeholder="RTN",
                        name="rtn",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
            ),

            # Teléfono del proveedor y Correo del proveedor
            rx.hstack(
                rx.vstack(
                    rx.text("Teléfono del proveedor", margin_bottom="5px"),
                    rx.input(
                        type="number",
                        placeholder="Teléfono del proveedor",
                        name="telefono_proveedor",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
                rx.vstack(
                    rx.text("Correo del proveedor", margin_bottom="5px"),
                    rx.input(
                        type="email",
                        placeholder="Correo del proveedor",
                        name="correo_proveedor",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
            ),

            # Información del Vendedor
            rx.text("Información del Vendedor", margin_top="30px", margin_bottom="35px"),

            # Primer nombre y Segundo nombre del vendedor
            rx.hstack(
                rx.vstack(
                    rx.text("Primer nombre del vendedor", margin_bottom="5px"),
                    rx.input(
                        type="text",
                        placeholder="Primer nombre del vendedor",
                        name="primer_nombre_vendedor",
                        margin_bottom="35px",
                        style={"width": "400px"}
                    ),
                ),
                rx.vstack(
                    rx.text("Segundo nombre del vendedor", margin_bottom="5px"),
                    rx.input(
                        type="text",
                        placeholder="Segundo nombre del vendedor",
                        name="segundo_nombre_vendedor",
                        margin_bottom="35px",
                        style={"width": "400px"}
                    ),
                ),
            ),

            # Primer apellido y Segundo apellido del vendedor
            rx.hstack(
                rx.vstack(
                    rx.text("Primer apellido del vendedor", margin_bottom="5px"),
                    rx.input(
                        type="text",
                        placeholder="Primer apellido del vendedor",
                        name="primer_apellido_vendedor",
                        margin_bottom="35px",
                        style={"width": "400px"}
                    ),
                ),
                rx.vstack(
                    rx.text("Segundo apellido del vendedor", margin_bottom="5px"),
                    rx.input(
                        type="text",
                        placeholder="Segundo apellido del vendedor",
                        name="segundo_apellido_vendedor",
                        margin_bottom="35px",
                        style={"width": "400px"}
                    ),
                ),
            ),

            # DNI del vendedor y Teléfono del vendedor
            rx.hstack(
                rx.vstack(
                    rx.text("DNI del vendedor", margin_bottom="5px"),
                    rx.input(
                        type="number",
                        placeholder="DNI del vendedor",
                        name="dni_vendedor",
                        margin_bottom="35px",
                        style={"width": "400px"}
                    ),
                ),
                rx.vstack(
                    rx.text("Teléfono del vendedor", margin_bottom="5px"),
                    rx.input(
                        type="number",
                        placeholder="Teléfono del vendedor",
                        name="telefono_vendedor",
                        margin_bottom="35px",
                        style={"width": "400px"}
                    ),
                ),
            ),

            # Correo del vendedor
            rx.vstack(
                rx.text("Correo del vendedor", margin_bottom="5px"),
                rx.input(
                    type="email",
                    placeholder="Correo del vendedor",
                    name="correo_vendedor",
                    margin_bottom="35px",
                    style={"width": "400px"}
                ),
            ),

            # Botón de enviar
            rx.hstack(
                rx.alert_dialog.root(
                    rx.alert_dialog.trigger(
                        rx.button("Guardar"),
                    ),
                    rx.alert_dialog.content(
                        rx.alert_dialog.title("Agregar proveedor"),
                        rx.alert_dialog.description(
                            "Confirmar y guardar proveedor.",
                        ),
                        rx.flex(
                            rx.alert_dialog.cancel(
                                boton_tres("x", "/alert", "Cancelar"),
                            ),
                            rx.alert_dialog.action(
                                boton_tres("save", "/alert", "Confirmar"),
                            ),
                            spacing="3",
                        ),
                    ),
                ),
                rx.alert_dialog.root(
                    rx.alert_dialog.trigger(
                        rx.button("Cancelar"),
                    ),
                    rx.alert_dialog.content(
                        rx.alert_dialog.title("Agregar proveedor"),
                        rx.alert_dialog.description(
                            "Descartar cambios.",
                        ),
                        rx.flex(
                            rx.alert_dialog.cancel(
                                boton_tres("x", "/alert", "Cancelar"),
                            ),
                            rx.alert_dialog.action(
                                boton_tres("save", "/alert", "Descartar"),
                            ),
                            spacing="3",
                        ),
                    ),
                )
                
###############################
            ),
        )
    )


def agregar_proveedor_page():
    return rx.container(
        formulario_agregar_proveedor(),
    )


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

        # Subir documentación y Seleccionar departamento en una misma fila
        rx.hstack(
            boton_dos("plus", "/proveedores/agregar_proveedor/subir_doc", "Agregar documento"),
            rx.select(
                [
                    "Francisco Morazán", #Estos datos seran estraídos de la base de datos
                    "Comayagua",
                    "Choluteca",
                    "Gracias a Dios",
                    "La Paz",
                    "El Paraíso",
                    "Copan",
                ],
                name="departamento",
                placeholder="Selecciona un departamento",
                margin_bottom="35px"
            ),
        ),

        # Dirección
        rx.input(
            type="text",
            placeholder="Dirección",
            name="direccion",
            multiline=True,  # Esto crea un área de texto multilínea
            rows=3,
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Nombre del proveedor
        rx.input(
            type="text",
            placeholder="Nombre del proveedor",
            name="nombre_proveedor",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # RTN (campo numérico)
        rx.input(
            type="number",
            placeholder="RTN",
            name="rtn",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Teléfono del proveedor y Correo del proveedor en la misma fila
        rx.hstack(
            rx.input(
                type="number",
                placeholder="Teléfono del proveedor",
                name="telefono_proveedor",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
            rx.input(
                type="email",
                placeholder="Correo del proveedor",
                name="correo_proveedor",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
        ),

        rx.text("Información del Vendedor", margin_top="30px", margin_bottom="35px"),  # Título para la sección de información del vendedor

        # Primer nombre y Segundo nombre del vendedor en la misma fila
        rx.hstack(
            rx.input(
                type="text",
                placeholder="Primer nombre del vendedor",
                name="primer_nombre_vendedor",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
            rx.input(
                type="text",
                placeholder="Segundo nombre del vendedor",
                name="segundo_nombre_vendedor",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
        ),

        # Primer apellido y Segundo apellido del vendedor en la misma fila
        rx.hstack(
            rx.input(
                type="text",
                placeholder="Primer apellido del vendedor",
                name="primer_apellido_vendedor",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
            rx.input(
                type="text",
                placeholder="Segundo apellido del vendedor",
                name="segundo_apellido_vendedor",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
        ),

        # DNI del vendedor
        rx.input(
            type="number",
            placeholder="DNI del vendedor",
            name="dni_vendedor",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Teléfono del vendedor (con área del país predefinida)
        rx.input(
            type="number",
            placeholder="Teléfono del vendedor",
            name="telefono_vendedor",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Correo del vendedor (con validación de correo electrónico)
        rx.input(
            type="email",
            placeholder="Correo del vendedor",
            name="correo_vendedor",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Botón de enviar
        rx.hstack(
            boton_tres("save","/alert","Guardar"),
            boton_tres("x","/alert","Cancelar"),
        ),
    )


def agregar_proveedor_page():
    return rx.container(
        formulario_agregar_proveedor(),
    )




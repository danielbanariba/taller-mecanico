# agregar_proveedor_page.py
from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.components.botones import boton_dos

import os

def formulario_agregar_proveedor():
    return rx.container(
        rx.text("Agregar Proveedor", size="3", margin_bottom="20px"),  # Título del formulario
        #Subir documentación
        rx.hstack(
            boton_dos("plus", "/proveedores/agregar_proveedor/subir_doc", "Agregar documento"),
        ),
        # Departamento (lista de selección)
        rx.select(
            [
                "Departamento 1",
                "Departamento 2",
                "Departamento 3",
            ],
            name="departamento",
            placeholder="Selecciona un departamento",
            margin_bottom="20px"
        ),

        # Dirección
        rx.input(
            type="text",
            placeholder="Dirección",
            name="direccion",
            multiline=True,  # Esto crea un área de texto multilínea
            rows=3,
            margin_bottom="20px"
        ),

        # Nombre del proveedor
        rx.input(
            type="text",
            placeholder="Nombre del proveedor",
            name="nombre_proveedor",
            margin_bottom="20px"
        ),

        # RTN (campo numérico)
        rx.input(
            type="number",
            placeholder="RTN",
            name="rtn",
            margin_bottom="20px"
        ),

        # Teléfono del proveedor (con área del país predefinida)
        rx.input(
            type="text",
            placeholder="Teléfono del proveedor",
            name="telefono_proveedor",
            margin_bottom="20px"
        ),

        # Correo del proveedor (con validación de correo electrónico)
        rx.input(
            type="email",
            placeholder="Correo del proveedor",
            name="correo_proveedor",
            margin_bottom="20px"
        ),

        rx.text("Información del Vendedor", margin_top="30px", margin_bottom="20px"),  # Título para la sección de información del vendedor
# Primer nombre del vendedor
        rx.input(
            type="text",
            placeholder="Primer nombre del vendedor",
            name="primer_nombre_vendedor",
            margin_bottom="20px"
        ),

        # Segundo nombre del vendedor
        rx.input(
            type="text",
            placeholder="Segundo nombre del vendedor",
            name="segundo_nombre_vendedor",
            margin_bottom="20px"
        ),

        # Primer apellido del vendedor
        rx.input(
            type="text",
            placeholder="Primer apellido del vendedor",
            name="primer_apellido_vendedor",
            margin_bottom="20px"
        ),

        # Segundo apellido del vendedor
        rx.input(
            type="text",
            placeholder="Segundo apellido del vendedor",
            name="segundo_apellido_vendedor",
            margin_bottom="20px"
        ),

        # DNI del vendedor
        rx.input(
            type="text",
            placeholder="DNI del vendedor",
            name="dni_vendedor",
            margin_bottom="20px"
        ),

        # Teléfono del vendedor (con área del país predefinida)
        rx.input(
            type="text",
            placeholder="Teléfono del vendedor (504+)",
            name="telefono_vendedor",
            margin_bottom="20px"
        ),

        # Correo del vendedor (con validación de correo electrónico)
        rx.input(
            type="email",
            placeholder="Correo del vendedor",
            name="correo_vendedor",
            margin_bottom="20px"
        ),

        # Botón de enviar
        rx.button("Enviar", type="submit", margin_top="20px"),
    )


"""#Errores sin no se llenan los campos

class FormErrorState(rx.State):
    nombre_proveedor: str
    primer_nombre_vendedor: str
    # Agrega más campos si necesitas validarlos

    @rx.var
    def is_error(self) -> bool:
        # Aquí puedes agregar tus propias validaciones según tus requisitos
        return len(self.nombre_proveedor) <= 3 or len(self.primer_nombre_vendedor) <= 3
        # Agrega más condiciones según sea necesario

def formulario_agregar_proveedor():
    return rx.container(
        rx.text("Agregar Proveedor", size="3", margin_bottom="20px"),  # Título del formulario
        # Subir documentación
        rx.hstack(
            boton_dos("plus", "/proveedores/agregar_proveedor/subir_doc", "Agregar documento"),
        ),
        # Departamento (lista de selección)
        rx.select(
            [
                "Departamento 1",
                "Departamento 2",
                "Departamento 3",
            ],
            name="departamento",
            placeholder="Selecciona un departamento",
            margin_bottom="20px"
        ),

        # Dirección
        rx.input(
            type="text",
            placeholder="Dirección",
            name="direccion",
            multiline=True,  # Esto crea un área de texto multilínea
            rows=3,
            margin_bottom="20px"
        ),

        # Nombre del proveedor con validación
        rx.chakra.form_control(
            rx.input(
                type="text",
                placeholder="Nombre del proveedor",
                name="nombre_proveedor",
                margin_bottom="20px",
                on_blur=FormErrorState.set_nombre_proveedor,
            ),
            rx.cond(
                FormErrorState.is_error,
                rx.chakra.form_error_message(
                    "El nombre del proveedor debe tener más de tres caracteres"
                ),
                rx.chakra.form_helper_text("Ingrese el nombre del proveedor"),
            ),
            is_invalid=FormErrorState.is_error,
            is_required=True,
        ),

        # RTN (campo numérico)
        rx.input(
            type="number",
            placeholder="RTN",
            name="rtn",
            margin_bottom="20px"
        ),

        # Teléfono del proveedor (con área del país predefinida)
        rx.input(
            type="text",
            placeholder="Teléfono del proveedor",
            name="telefono_proveedor",
            margin_bottom="20px"
        ),

        # Correo del proveedor (con validación de correo electrónico)
        rx.input(
            type="email",
            placeholder="Correo del proveedor",
            name="correo_proveedor",
            margin_bottom="20px"
        ),

        # Información del Vendedor
        rx.text("Información del Vendedor", margin_top="30px", margin_bottom="20px"),  # Título para la sección de información del vendedor

        # Primer nombre del vendedor con validación
        rx.chakra.form_control(
            rx.input(
                type="text",
                placeholder="Primer nombre del vendedor",
                name="primer_nombre_vendedor",
                margin_bottom="20px",
                on_blur=FormErrorState.set_primer_nombre_vendedor,
            ),
            rx.cond(
                FormErrorState.is_error,
                rx.chakra.form_error_message(
                    "El primer nombre del vendedor debe tener más de tres caracteres"
                ),
                rx.chakra.form_helper_text("Ingrese el primer nombre del vendedor"),
            ),
            is_invalid=FormErrorState.is_error,
            is_required=True,
        ),

        # Segundo nombre del vendedor
        rx.input(
            type="text",
            placeholder="Segundo nombre del vendedor",
            name="segundo_nombre_vendedor",
            margin_bottom="20px"
        ),

        # Primer apellido del vendedor
        rx.input(
            type="text",
            placeholder="Primer apellido del vendedor",
            name="primer_apellido_vendedor",
            margin_bottom="20px"
        ),

        # Segundo apellido del vendedor
        rx.input(
            type="text",
            placeholder="Segundo apellido del vendedor",
            name="segundo_apellido_vendedor",
            margin_bottom="20px"
        ),

        # DNI del vendedor
        rx.input(
            type="text",
            placeholder="DNI del vendedor",
            name="dni_vendedor",
            margin_bottom="20px"
        ),

        # Teléfono del vendedor (con área del país predefinida)
        rx.input(
            type="text",
            placeholder="Teléfono del vendedor (504+)",
            name="telefono_vendedor",
            margin_bottom="20px"
        ),

        # Correo del vendedor (con validación de correo electrónico)
        rx.input(
            type="email",
            placeholder="Correo del vendedor",
            name="correo_vendedor",
            margin_bottom="20px"
        ),

        # Botón de enviar
        rx.button("Enviar", type="submit", margin_top="20px"),
    )
"""



def agregar_proveedor_page():
    return rx.container(
        formulario_agregar_proveedor(),
    )




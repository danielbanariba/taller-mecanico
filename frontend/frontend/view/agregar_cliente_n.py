# agregar_proveedor_page.py
from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.components.botones import boton_dos

import os

def formulario_agregar_clientes_n():
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

        # Nombre del cliente
        rx.input(
            type="text",
            placeholder="Nombre del Cliente",
            name="nombre_cliente",
            margin_bottom="20px"
        ),

        # RTN (campo numérico)
        rx.input(
            type="number",
            placeholder="RTN",
            name="rtn",
            margin_bottom="20px"
        ),

        # Teléfono del cliente
        rx.input(
            type="text",
            placeholder="Teléfono del proveedor",
            name="telefono_proveedor",
            margin_bottom="20px"
        ),

        # Correo del cliente (con validación de correo electrónico)
        rx.input(
            type="email",
            placeholder="Correo del Cliente",
            name="correo_cliente",
            margin_bottom="20px"
        ),

        rx.text("Información del Cliente", margin_top="30px", margin_bottom="20px"),  # Título para la sección de información del vendedor
# Primer nombre del cliente
        rx.input(
            type="text",
            placeholder="Primer nombre del Cliente",
            name="primer_nombre_cliente",
            margin_bottom="20px"
        ),

        # Segundo nombre del Cliente
        rx.input(
            type="text",
            placeholder="Segundo nombre del Cliente",
            name="segundo_nombre_cliente",
            margin_bottom="20px"
        ),

        # Primer apellido del Cliente
        rx.input(
            type="text",
            placeholder="Primer apellido del Cliente",
            name="primer_apellido_cliente",
            margin_bottom="20px"
        ),

        # Segundo apellido del Cliente
        rx.input(
            type="text",
            placeholder="Segundo apellido del Cliente",
            name="segundo_apellido_cliente",
            margin_bottom="20px"
        ),

        # DNI del Cliente
        rx.input(
            type="text",
            placeholder="DNI del Cliente",
            name="dni_cliente",
            margin_bottom="20px"
        ),

        # Teléfono del Cliente (con área del país predefinida)
        rx.input(
            type="text",
            placeholder="Teléfono del Cliente (504+)",
            name="telefono_cliente",
            margin_bottom="20px"
        ),

        # Correo del vendedor (con validación de correo electrónico)
        rx.input(
            type="email",
            placeholder="Correo del Cliente",
            name="correo_Cliente",
            margin_bottom="20px"
        ),

        # Botón de enviar
        rx.button("Enviar", type="submit", margin_top="20px"),
    )


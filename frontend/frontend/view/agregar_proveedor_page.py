# agregar_proveedor_page.py
from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH

import os

def formulario_agregar_proveedor():
    return rx.container(
        rx.text("Agregar Proveedor", size="3", margin_bottom="20px"),  # Título del formulario

        # Departamento (lista de selección)
        rx.select(
            options=[
                {"label": "Departamento 1", "value": "departamento1"},
                {"label": "Departamento 2", "value": "departamento2"},
                {"label": "Departamento 3", "value": "departamento3"},
            ],
            name="departamento",
            placeholder="Selecciona un departamento",
            margin_bottom="20px"
        ),

        # Dirección
        rx.textarea(
            placeholder="Dirección",
            name="direccion",
            rows="3",
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
            placeholder="Teléfono del proveedor (504+)",
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

def agregar_proveedor_page():
    return rx.container(
        formulario_agregar_proveedor(),
    )
    
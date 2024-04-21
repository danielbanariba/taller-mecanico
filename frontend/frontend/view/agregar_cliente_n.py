# agregar_clientes_page.py
from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.components.botones import boton_tres

import os

def formulario_agregar_cliente_natural():
    return rx.container(
        rx.text("Agregar Cliente Natural", size="3", margin_bottom="35px"),  # Título del formulario

        # Lista desplegable para seleccionar la naturaleza del cliente
        rx.select(
            [
                "Persona Natural",
            ],
            name="naturaleza_cliente",
            placeholder="Selecciona la naturaleza del cliente",
            margin_bottom="35px"
        ),

        # Departamento (lista desplegable)
        rx.select(
            [
                "Francisco Morazán",
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

        # Dirección del cliente
        rx.input(
            type="text",
            placeholder="Dirección del cliente",
            name="direccion_cliente",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Nombre del cliente: Primer nombre y Segundo nombre en la misma fila
        rx.hstack(
            rx.input(
                type="text",
                placeholder="Primer nombre del cliente",
                name="primer_nombre_cliente",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
            rx.input(
                type="text",
                placeholder="Segundo nombre del cliente",
                name="segundo_nombre_cliente",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
        ),

        # Apellidos del cliente: Primer apellido y Segundo apellido en la misma fila
        rx.hstack(
            rx.input(
                type="text",
                placeholder="Primer apellido del cliente",
                name="primer_apellido_cliente",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
            rx.input(
                type="text",
                placeholder="Segundo apellido del cliente",
                name="segundo_apellido_cliente",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
        ),

        # Correo electrónico del cliente
        rx.input(
            type="email",
            placeholder="Correo electrónico del cliente",
            name="correo_cliente",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Teléfono del cliente
        rx.input(
            type="number",
            placeholder="Teléfono del cliente",
            name="telefono_cliente",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Botón de guardar y cancelar
        rx.hstack(
            boton_tres("save", "/alert", "Guardar"),
            boton_tres("x", "/alert", "Cancelar"),
        ),
    )


def agregar_cliente_natural_page():
    return rx.container(
        formulario_agregar_cliente_natural(),
    )

from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.components.botones import boton_tres


import os


def formulario_agregar_empresa():
    return rx.container(
        rx.text("Agregar Empresa como Cliente", size="3", margin_bottom="35px"),  # Título del formulario

        # Lista desplegable para seleccionar la naturaleza del cliente
        rx.select(
            [
                "Persona Jurídica",
                "Persona Natural",
            ],
            name="naturaleza_cliente",
            placeholder="Selecciona la naturaleza del cliente",
            margin_bottom="35px"
        ),

        # Nombre de la empresa
        rx.input(
            type="text",
            placeholder="Nombre de la empresa",
            name="nombre_empresa",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
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

        # Dirección de la empresa
        rx.input(
            type="text",
            placeholder="Dirección de la empresa",
            name="direccion_empresa",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # RTN de la empresa
        rx.input(
            type="number",
            placeholder="RTN de la empresa",
            name="rtn_empresa",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Correo de la empresa
        rx.input(
            type="email",
            placeholder="Correo de la empresa",
            name="correo_empresa",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Representante de la empresa: Primer nombre y Segundo nombre en la misma fila
        rx.hstack(
            rx.input(
                type="text",
                placeholder="Primer nombre del representante",
                name="primer_nombre_representante",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
            rx.input(
                type="text",
                placeholder="Segundo nombre del representante",
                name="segundo_nombre_representante",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
        ),

        # Representante de la empresa: Primer apellido y Segundo apellido en la misma fila
        rx.hstack(
            rx.input(
                type="text",
                placeholder="Primer apellido del representante",
                name="primer_apellido_representante",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
            rx.input(
                type="text",
                placeholder="Segundo apellido del representante",
                name="segundo_apellido_representante",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
        ),

        # Correo del contacto de la empresa
        rx.input(
            type="email",
            placeholder="Correo del contacto de la empresa",
            name="correo_contacto_empresa",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Teléfono del contacto de la empresa
        rx.input(
            type="number",
            placeholder="Teléfono del contacto de la empresa",
            name="telefono_contacto_empresa",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Botón de enviar y cancelar
        rx.hstack(
            boton_tres("save", "/alert", "Guardar"),
            boton_tres("x", "/alert", "Cancelar"),
        ),
    )


def agregar_empresa_page():
    return rx.container(
        formulario_agregar_empresa(),
    )

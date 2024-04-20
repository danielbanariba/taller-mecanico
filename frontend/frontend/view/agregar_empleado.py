from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.components.botones import boton_dos
from frontend.components.botones import boton_tres
from frontend.view.modificar_empleado import detalles_proveedor

import os

def formulario_agregar_empleado():
    return rx.container(
        rx.text("Agregar Empleado", size="3", margin_bottom="35px"),  # Título del formulario

        # Subir documentación y Seleccionar departamento en una misma fila
        rx.hstack(
            boton_dos("plus", "/empleados/agregar_empleado/subir_doc", "Agregar documento"),
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

        rx.select(
                [
                    "administrador", #Estos datos seran estraídos de la base de datos
                    "Encargada Administrativa",
                    "Asesor de servicio",
                    "Tecnico automotriz",
                ],
                name="cargo",
                placeholder="Selecciona un cargo",
                margin_bottom="35px"
            ),


            # Primer nombre y Segundo nombre del vendedor en la misma fila
        rx.hstack(
            rx.input(
                type="text",
                placeholder="Primer nombre del empleado",
                name="primer_nombre_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
            rx.input(
                type="text",
                placeholder="Segundo nombre del empleado",
                name="segundo_nombre_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
        ),

        # Primer apellido y Segundo apellido del vendedor en la misma fila
        rx.hstack(
            rx.input(
                type="text",
                placeholder="Primer apellido del empleado",
                name="primer_apellido_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
            rx.input(
                type="text",
                placeholder="Segundo apellido del empleado",
                name="segundo_apellido_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
        ),


        # DNI del empleado y RTN del empleado en la misma fila
        rx.hstack(
            rx.input(
                type="number",
                placeholder="DNI del empleado",
                name="dni_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
            rx.input(
                type="number",
                placeholder="RTN",
                name="rtn",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
        ),


        # Teléfono del empleado y Correo del empleado en la misma fila
        rx.hstack(
            rx.input(
                type="number",
                placeholder="Teléfono del empleado",
                name="telefono_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
            rx.input(
                type="email",
                placeholder="Correo del empleado",
                name="correo_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
        ),


        rx.select(
                [
                    "Soltero", #Estos datos seran estraídos de la base de datos
                    "Casado",
                    "Divorciado",
                    "Union Libre",
                ],
                name="estado_civil",
                placeholder="Selecciona un estado civil",
                margin_bottom="35px"
            ),

        # Fecha de nacimiento del empleado
        rx.input(
            type="text",
            placeholder="Fecha de nacimiento (YYYY-MM-DD)",
            name="fecha_nacimiento",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Nombre de contacto de emergencia
        rx.input(
            type="text",
            placeholder="Nombre del contacto emergencia",
            name="nombre_contacto_emergencia",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Teléfono de contacto de emergencia (con área del país predefinida)
        rx.input(
            type="number",
            placeholder="Teléfono de contaco de emergenciaa",
            name="telefono_contaco_emergencia",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),


        rx.select(
                [
                    "Padre", #Estos datos seran estraídos de la base de datos
                    "Madre",
                    "Herman@",
                    "Ti@",
                ],
                name="parentesco",
                placeholder="Selecciona un parentesco",
                margin_bottom="35px"
            ),


        # Botón de enviar
        rx.hstack(
            boton_tres("save","/alert","Guardar"),
            boton_tres("x","/alert","Cancelar"),
        ),
    )


def agregar_empleado_page():
    return rx.container(
        formulario_agregar_empleado(),
    )
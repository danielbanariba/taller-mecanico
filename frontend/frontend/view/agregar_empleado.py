from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.components.botones import boton_dos
from frontend.components.botones import boton_tres


import os



def formulario_agregar_empleado():
    return rx.container(
        rx.flex(
            rx.center(rx.text("Agregar empleado"), bg="lightblue"), 
            width="800px",
            margin_top="25px",
            margin_bottom="20px",
        ),
        # Subir documentación y Seleccionar departamento en la misma fila
        rx.hstack(
            boton_tres("plus", "/empleados/agregar_empleado/subir_doc", "Agregar documento"),
            rx.select(
                [
                    "Atlántida",
                    "Choluteca",
                    "Colón",
                    "Comayagua",
                    "Copán",
                    "Cortés",
                    "El Paraíso",
                    "Francisco Morazán",
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
                    style={"width": "800px"}
                ),
            ),

            # Cargo
            rx.vstack(
                rx.text("Cargo", margin_bottom="5px"),
                rx.select(
                    [
                        "Administrador",
                        "Encargada Administrativa",
                        "Asesor de Servicio",
                        "Técnico Automotriz",
                    ],
                    name="cargo",
                    placeholder="Selecciona un cargo",
                    margin_bottom="20px",
                    style={"width": "400px"}
                ),
            ),

            # Nombres
            rx.hstack(
                rx.vstack(
                    rx.text("Primer Nombre ", margin_bottom="5px"),
                    rx.input(
                        type="text",
                        placeholder="Primer Nombre ",
                        name="primer_nombre_empleado",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
                rx.vstack(
                    rx.text("Segundo Nombre ", margin_bottom="5px"),
                    rx.input(
                        type="text",
                        placeholder="Segundo Nombre ",
                        name="segundo_nombre_empleado",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
            ),

            # Apellidos
            rx.hstack(
                rx.vstack(
                    rx.text("Primer Apellido ", margin_bottom="5px"),
                    rx.input(
                        type="text",
                        placeholder="Primer Apellido ",
                        name="primer_apellido_empleado",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
                rx.vstack(
                    rx.text("Segundo Apellido ", margin_bottom="5px"),
                    rx.input(
                        type="text",
                        placeholder="Segundo Apellido ",
                        name="segundo_apellido_empleado",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
            ),

            # DNI y RTN
            rx.hstack(
                rx.vstack(
                    rx.text("DNI ", margin_bottom="5px"),
                    rx.input(
                        type="number",
                        placeholder="DNI ",
                        name="dni_empleado",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
                rx.vstack(
                    rx.text("RTN ", margin_bottom="5px"),
                    rx.input(
                        type="number",
                        placeholder="RTN ",
                        name="rtn",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
            ),

            # Teléfono y Correo 
            rx.hstack(
                rx.vstack(
                    rx.text("Teléfono ", margin_bottom="5px"),
                    rx.input(
                        type="number",
                        placeholder="Teléfono ",
                        name="telefono_empleado",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
                rx.vstack(
                    rx.text("Correo ", margin_bottom="5px"),
                    rx.input(
                        type="email",
                        placeholder="Correo ",
                        name="correo_empleado",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
            ),
            rx.hstack(
                # Estado Civil
                rx.vstack(
                    rx.text("Estado Civil", margin_bottom="5px"),
                    rx.select(
                        [
                            "Soltero",
                            "Casado",
                            "Divorciado",
                            "Unión Libre",
                        ],
                        name="estado_civil",
                        placeholder="Selecciona un estado civil",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),

                # Fecha de Nacimiento
                rx.vstack(
                    rx.text("Fecha de Nacimiento", margin_bottom="5px"),
                    rx.input(
                        type="text",
                        placeholder="Fecha de Nacimiento (YYYY-MM-DD)",
                        name="fecha_nacimiento",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
            ),

            # Información de Contacto de Emergencia
            rx.flex(
                rx.center(rx.text("Infromación del contacto de emergencia"), bg="lightblue"), 
                width="800px",
                margin_top="25px",
                margin_bottom="20px",
            ),
            # Parentesco
            rx.vstack(
                rx.text("Parentesco con el Contacto de Emergencia", margin_bottom="5px"),
                rx.select(
                    [
                        "Padre",
                        "Madre",
                        "Hermano",
                        "Tío",
                    ],
                    name="parentesco",
                    placeholder="Selecciona un parentesco",
                    margin_bottom="20px",
                    style={"width": "400px"}
                ),
            ),

            rx.hstack(
                # Nombre y Teléfono del Contacto de Emergencia
                rx.vstack(
                    rx.text("Nombre del Contacto de Emergencia", margin_bottom="5px"),
                    rx.input(
                        type="text",
                        placeholder="Nombre del Contacto de Emergencia",
                        name="nombre_contacto_emergencia",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
                rx.vstack(
                    rx.text("Teléfono del Contacto de Emergencia", margin_bottom="5px"),
                    rx.input(
                        type="number",
                        placeholder="Teléfono del Contacto de Emergencia",
                        name="telefono_contacto_emergencia",
                        margin_bottom="20px",
                        style={"width": "400px"}
                    ),
                ),
            ),

        ),

        # Botón de enviar
        rx.hstack(
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button("Guardar", color_scheme="purple"),
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Agregar empleado"),
                    rx.alert_dialog.description(
                        "Confirmar y guardar empleado.",
                    ),
                    rx.flex(
                        rx.alert_dialog.cancel(
                            rx.button("Cancelar"),
                            style={
                                        'width': '150px', 
                                        'height': '30px',
                                        'backgroundColor': '#b39eff',
                                        'cursor': 'pointer',
                                        'fontSize': '15px',
                                        ':hover': {
                                            'backgroundColor': '#9f87de',
                                            'transition': '0.3s',
                                        },
                                    },
                        ),
                        rx.alert_dialog.action(
                            boton_tres("check", "/empleados", "Confirmar"),
                        ),
                        spacing="3",
                    ),
                ),
            ),

            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button("Descartar", color_scheme="purple"),
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Agregar proveedor"),
                    rx.alert_dialog.description(
                        "Descartar cambios.",
                    ),
                    rx.flex(
                        rx.alert_dialog.cancel(
                            rx.button("Cancelar"),
                            style={
                                    'width': '150px', 
                                    'height': '30px',
                                    'backgroundColor': '#b39eff',
                                    'cursor': 'pointer',  # Cambia el cursor a una mano
                                    'margin': '0',
                                    'fontSize': '15px',  # Ajusta el tamaño del texto aquí
                                    ':hover': {
                                        'backgroundColor': '#9f87de',  # Cambia el color de fondo cuando se pasa el cursor por encima
                                        'transition': '0.3s',
                                        },
                                },
                        ),
                        rx.alert_dialog.action(
                            boton_tres("check", "/proveedores", "Confirmar"),
                        ),
                        spacing="3",
                    ),
                ),
            ),
        ),
    )


def agregar_empleado_page():
    return rx.container(
        formulario_agregar_empleado(),
    )

"""def formulario_agregar_empleado():
    return rx.container(
        #rx.text("Agregar Empleado", size="3", margin_bottom="35px"),  # Título del formulario
        #rx.badge("Agregar empleado", size="2",variant="soft"),
        rx.flex(
            rx.center(rx.text("Agregar empleado"), bg="lightblue"), 
            width="800px",
            margin_top="25px",
            margin_bottom="20px",
        ),
        # Subir documentación y Seleccionar departamento en una misma fila
        rx.hstack(
            boton_tres("plus", "/empleados/agregar_empleado/subir_doc", "Agregar documento"),
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
                style={"width": "400px", "high": "100px"}
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
                placeholder="Primer nombre ",
                name="primer_nombre_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
            rx.input(
                type="text",
                placeholder="Segundo nombre ",
                name="segundo_nombre_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
        ),

        # Primer apellido y Segundo apellido del vendedor en la misma fila
        rx.hstack(
            rx.input(
                type="text",
                placeholder="Primer apellido ",
                name="primer_apellido_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
            rx.input(
                type="text",
                placeholder="Segundo apellido ",
                name="segundo_apellido_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 200px
            ),
        ),


        # DNI  y RTN  en la misma fila
        rx.hstack(
            rx.input(
                type="number",
                placeholder="DNI ",
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


        # Teléfono  y Correo  en la misma fila
        rx.hstack(
            rx.input(
                type="number",
                placeholder="Teléfono ",
                name="telefono_empleado",
                margin_bottom="35px",
                style={"width": "400px"}  # Ancho de 400px
            ),
            rx.input(
                type="email",
                placeholder="Correo ",
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

        # Fecha de nacimiento 
        rx.input(
            type="text",
            placeholder="Fecha de nacimiento (YYYY-MM-DD)",
            name="fecha_nacimiento",
            margin_bottom="35px",
            style={"width": "400px"}  # Ancho de 400px
        ),

        # Nombre de contacto de emergencia
        rx.flex(
            rx.center(rx.text("Información del contacto de emergencia"), bg="lightblue"), 
            width="800px",
            margin_top="25px",
            margin_bottom="20px",
        ),
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
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button("Guardar", color_scheme="purple"),
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Agregar proveedor"),
                    rx.alert_dialog.description(
                        "Confirmar y guardar proveedor.",
                    ),
                    rx.flex(
                        rx.alert_dialog.cancel(
                            rx.button("Cancelar"),
                            style={
                                        'width': '150px', 
                                        'height': '30px',
                                        'backgroundColor': '#b39eff',
                                        'cursor': 'pointer',  # Cambia el cursor a una mano
                                        'margin': '0',
                                        'fontSize': '15px',  # Ajusta el tamaño del texto aquí
                                        ':hover': {
                                            'backgroundColor': '#9f87de',  # Cambia el color de fondo cuando se pasa el cursor por encima
                                            'transition': '0.3s',
                                            },
                                    },
                        ),
                        rx.alert_dialog.action(
                            boton_tres("check", "/empleados", "Confirmar"),
                        ),
                        spacing="3",
                    ),
                ),
            ),
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button("Descartar", color_scheme="purple"),
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Agregar proveedor"),
                    rx.alert_dialog.description(
                        "Descartar cambios.",
                    ),
                    rx.flex(
                        rx.alert_dialog.cancel(
                            rx.button("Cancelar"),
                            style={
                                        'width': '150px', 
                                        'height': '30px',
                                        'backgroundColor': '#b39eff',
                                        'cursor': 'pointer',  # Cambia el cursor a una mano
                                        'margin': '0',
                                        'fontSize': '15px',  # Ajusta el tamaño del texto aquí
                                        ':hover': {
                                            'backgroundColor': '#9f87de',  # Cambia el color de fondo cuando se pasa el cursor por encima
                                            'transition': '0.3s',
                                            },
                                    },
                        ),
                        rx.alert_dialog.action(
                            boton_tres("check", "/empleados", "Descartar"),
                        ),
                        spacing="3",
                    ),
                ),
            ),#
        ),
    )


def agregar_empleado_page():
    return rx.container(
        formulario_agregar_empleado(),
    )"""
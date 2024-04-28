from typing import List
import pandas as pd
import reflex as rx
from frontend.view.navbar import navbar
from frontend.styles.styles import Size, MAX_WIDTH
from frontend.components.botones import boton_dos
from frontend.components.botones import boton_tres
from frontend.view.modificar_proveedor import detalles_proveedor


# Opciones para el selector
options: list[str] = ["Natural", "Jurídico"]

# Estado para el selector
class SetterState1(rx.State):
    selected: str = "Natural"  # Valor inicial

    def change(self, value):
        self.selected = value  # Cambiar el valor del estado


# Formulario 1 cliente natural
def formulario_cliente_natural():
    return rx.vstack(
        rx.text("Cliente natural", size="4", margin_bottom="35px"),
        
            rx.text("Agregar Cliente", size="3", margin_bottom="35px"),  

            # Subir documentación y Seleccionar departamento en la misma fila
            rx.hstack(
                boton_dos("plus", "/clientes/agregar_cliente/subir_doc", "Agregar documento"),
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


                # Primer nombre y Segundo nombre del vendedor
                rx.hstack(
                    rx.vstack(
                        rx.text("Primer nombre ", margin_bottom="5px"),
                        rx.input(
                            type="text",
                            placeholder="Primer nombre ",
                            name="primer_nombre_vendedor",
                            margin_bottom="35px",
                            style={"width": "400px"}
                        ),
                    ),
                    rx.vstack(
                        rx.text("Segundo nombre ", margin_bottom="5px"),
                        rx.input(
                            type="text",
                            placeholder="Segundo nombre ",
                            name="segundo_nombre_vendedor",
                            margin_bottom="35px",
                            style={"width": "400px"}
                        ),
                    ),
                ),

                # Primer apellido y Segundo apellido 
                rx.hstack(
                    rx.vstack(
                        rx.text("Primer apellido ", margin_bottom="5px"),
                        rx.input(
                            type="text",
                            placeholder="Primer apellido ",
                            name="primer_apellido_vendedor",
                            margin_bottom="35px",
                            style={"width": "400px"}
                        ),
                    ),
                    rx.vstack(
                        rx.text("Segundo apellido ", margin_bottom="5px"),
                        rx.input(
                            type="text",
                            placeholder="Segundo apellido ",
                            name="segundo_apellido_vendedor",
                            margin_bottom="35px",
                            style={"width": "400px"}
                        ),
                    ),
                ),

                # DNI  y Teléfono 
                rx.hstack(
                    rx.vstack(
                        rx.text("DNI ", margin_bottom="5px"),
                        rx.input(
                            type="number",
                            placeholder="DNI ",
                            name="dni_vendedor",
                            margin_bottom="35px",
                            style={"width": "400px"}
                        ),
                    ),
                    rx.vstack(
                        rx.text("Teléfono ", margin_bottom="5px"),
                        rx.input(
                            type="number",
                            placeholder="Teléfono ",
                            name="telefono_vendedor",
                            margin_bottom="35px",
                            style={"width": "400px"}
                        ),
                    ),
                ),

                # Correo 
                rx.vstack(
                    rx.text("Correo ", margin_bottom="5px"),
                    rx.input(
                        type="email",
                        placeholder="Correo ",
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
                    
   
                ),
            )
        
    )


# Formulario 2
def formulario_empresa():
    return rx.vstack(
        rx.text("Empresa"),
        
            rx.text("Agregar Cliente", size="3", margin_bottom="35px"),  # Título del formulario

            # Subir documentación y Seleccionar departamento en la misma fila
            rx.hstack(
                boton_dos("plus", "/clientes/agregar_cliente/subir_doc", "Agregar documento"),
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
                        rx.text("Nombre de la empresa ", margin_bottom="5px"),
                        rx.input(
                            type="text",
                            placeholder="Nombre del ",
                            name="nombre_",
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

                # Teléfono del  y Correo del 
                rx.hstack(
                    rx.vstack(
                        rx.text("Teléfono", margin_bottom="5px"),
                        rx.input(
                            type="number",
                            placeholder="Teléfono del ",
                            name="telefono_",
                            margin_bottom="20px",
                            style={"width": "400px"}
                        ),
                    ),
                    rx.vstack(
                        rx.text("Correo", margin_bottom="5px"),
                        rx.input(
                            type="email",
                            placeholder="Correo del ",
                            name="correo_",
                            margin_bottom="20px",
                            style={"width": "400px"}
                        ),
                    ),
                ),

                
                # Botón de enviar
                rx.hstack(
                    rx.alert_dialog.root(
                        rx.alert_dialog.trigger(
                            rx.button("Guardar"),
                        ),
                        rx.alert_dialog.content(
                            rx.alert_dialog.title("Agregar "),
                            rx.alert_dialog.description(
                                "Confirmar y guardar.",
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
                            rx.alert_dialog.title("Agregar "),
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
                    
   
                ),
            )
        

    )


# Selector para cargar el formulario correspondiente
def form_selector():
    return rx.cond(
        SetterState1.selected == "Natural",
        formulario_cliente_natural(),  # Si es "1", mostrar Formulario 1
        formulario_empresa(),  # Si no, mostrar Formulario 2
    )


# Componente principal con selector y formulario condicional
def code_setter():
    return rx.vstack(
        rx.select(
            options,
            on_change=lambda value: SetterState1.change(value),  # Cambiar estado
        ),
        form_selector(),  # Renderizar el formulario correspondiente
    )


def agregar_cliente_page():
    return rx.container(
        code_setter(),
    )

"""def formulario_agregar_cliente():
    return rx.container(
        rx.text("Agregar Cliente", size="3", margin_bottom="35px"),  # Título del formulario

        # Subir documentación y Seleccionar departamento en la misma fila
        rx.hstack(
            boton_dos("plus", "/clientes/agregar_cliente/subir_doc", "Agregar documento"),
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

        # Campos de entrada para los es
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

            # Información 
            rx.text("Información ", margin_top="30px", margin_bottom="35px"),

            # Primer nombre y Segundo nombre 
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


def agregar_cliente_page():
    return rx.container(
        formulario_agregar_cliente(),
    )"""


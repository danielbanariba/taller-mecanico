import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inicio import Inicio
from frontend.view.proveedores import Proveedores
from frontend.components.botones import boton_dos
from frontend.view.agregar_proveedor import formulario_agregar_proveedor
from frontend.view.modificar_proveedor import detalles_proveedor
from frontend.view.subir_doc import Subir_DOC
from frontend.components.botones import boton #para los botones de cada inicio de módulo, agregar, modificar, etc...
from frontend.components.botones import boton_dos

# Página de proveedor
def proveedores_page():
    return rx.vstack(
        navbar(),
        rx.hstack(  # Mantenemos los elementos en una fila
            Inicio(),
            rx.vstack(  # Los botones y la tabla se colocan verticalmente uno encima del otro
                # Botones para agregar, modificar y listar proveedores
                rx.hstack(
                    boton_dos("plus", "/proveedores/agregar_proveedor", "Agregar proveedor"),
                    boton_dos("plus", "/proveedores/modificar_proveedor","Modificar proveedor"),
                    boton_dos("plus", "/proveedores/listado_proveedor","Listado proveedores")
                ),
                # Separador entre los botones y la tabla
                rx.divider(),
                # Contenedor flexible para la tabla
                rx.container(
                    Proveedores(),
                    style={
                        "overflow-x": "auto",  # Agrega desplazamiento horizontal si es necesario
                        "width": "900px",  # Establece el ancho en 830px
                    }
                ),
            ),
        ),
    )
    

#Página de agregar proveedores
def agregar_proveedor_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            formulario_agregar_proveedor(),   
        ),
    )

#Página de modificar proveedor
def modificar_proveedor_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            detalles_proveedor(),   
        ),
    )
#Página de agregar o subir socumentación 
def agregar_doc_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            Subir_DOC(),   
        ),
    )

def listado_proveedor_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            #Inicio(),
            Proveedores(),   
        ),
    )
import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inventario import Inventario
from frontend.view.inicio import Inicio
from frontend.view.pantalla_dashboard import grafica_de_barras, grafica_lineal
from frontend.view.empleados import Empleados
from frontend.view.proveedores import Proveedores
from frontend.login import Login
from frontend.view.agregar_proveedor import formulario_agregar_empleado
from frontend.view.modificar_proveedor import detalles_empleado
from frontend.view.agregar_proveedor import formulario_agregar_proveedor
from frontend.view.modificar_proveedor import detalles_proveedor
from frontend.view.subir_doc import Subir_DOC
from frontend.components.botones import boton #para los botones de cada inicio de módulo, agregar, modificar, etc...
from frontend.components.botones import boton_dos
import frontend.URL as URL
from frontend.view.error_404 import error_404

#Página de inicio 
def login():
    return Login()


#Pagina de estadisticas
def estadisticas():
    return rx.vstack(
        navbar(),
        rx.hstack(
            Inicio(),
            rx.hstack(
                grafica_lineal(),
                grafica_de_barras()
            )
        )
    )


#Página de ejemplo
def about():
    return rx.text("About Page")


#Página de inicio
def inicio_page():
    return rx.vstack(
        navbar(),
        Inicio(),   
    )


#Página de inventario
def inventario_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            Inventario(),   
        ),
    )

# Página de empleado
def proveedores_page():
    return rx.vstack(
        navbar(),
        rx.hstack(  # Mantenemos los elementos en una fila
            Inicio(),
            rx.vstack(  # Los botones y la tabla se colocan verticalmente uno encima del otro
                # Botones para agregar, modificar y listar proveedores
                rx.hstack(
                    boton_dos("plus", "/empleados/agregar_empleado", "Agregar empleado"),
                    boton_dos("plus", "/empleados/modificar_empleado","Modificar empleado"),
                    boton_dos("plus", "/empleados/listado_empleado","Listado empleados")
                ),
                # Separador entre los botones y la tabla
                rx.divider(),
                # Contenedor flexible para la tabla
                rx.container(
                    Empleados(),
                    style={
                        "overflow-x": "auto",  # Agrega desplazamiento horizontal si es necesario
                        "width": "900px",  # Establece el ancho en 830px
                    }
                ),
            ),
        ),
    )

#Página de agregar proveedores
def agregar_empleado_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            formulario_agregar_empleado(),   
        ),
    )
#Página de modificar proveedor
def modificar_empleado_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            detalles_empleado(),   
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

def listado_empleado_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            #Inicio(),
            Empleados(),   
        ),
    )



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
  
# Crea la aplicación
app = rx.App()

#Genera las url o los directorios de la paginas correspondientes
app.add_page(login, route="/")
app.add_page(estadisticas, route="/estadisticas")
app.add_page(about)
app.add_page(inventario_page, route="/inventario")
app.add_page(inicio_page, route="/inicio")
app.add_page(proveedores_page, route="/empleados")
app.add_page(agregar_proveedor_page, route="/empleados/agregar_empleado") 
app.add_page(modificar_proveedor_page, route="/empleados/modificar_empleado") 
app.add_page(listado_proveedor_page, route="/empleados/listado_empleado") 
app.add_page(agregar_doc_page, route="/empleados/agregar_empleado/subir_doc")
app.add_page(agregar_doc_page, route="/empleados/agregar_empleado/subir_doc")
app.add_page(proveedores_page, route="/proveedores")
app.add_page(agregar_proveedor_page, route="/proveedores/agregar_proveedor") #Redirige al formulario para agregar un proveedor
app.add_page(modificar_proveedor_page, route="/proveedores/modificar_proveedor") 
app.add_page(listado_proveedor_page, route="/proveedores/listado_proveedor") 
app.add_page(agregar_doc_page, route="/proveedores/agregar_proveedor/subir_doc")
app.add_page(agregar_doc_page, route="/proveedores/agregar_proveedor/subir_doc")


#404 error personalizado
# Define tu componente personalizado para la página 404
def custom_404_component():
    return rx.text("Lo sentimos, la página que estás buscando no se pudo encontrar.")


# Ahora, puedes llamar al método para definir tu página 404 personalizada
app.add_custom_404_page(
    component=error_404, 
    title='404 - Página no encontrada', 
    image='mi_imagen_404.ico', 
    description='La página que estás buscando no existe.'
)

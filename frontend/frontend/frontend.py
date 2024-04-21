import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inventario import Inventario
from frontend.view.inicio import Inicio
from frontend.view.pantalla_dashboard import grafica_de_barras, grafica_lineal
from frontend.view.proveedores import Proveedores
from frontend.login import Login
from frontend.components.botones import boton_dos
from frontend.view.agregar_proveedor import formulario_agregar_proveedor
from frontend.view.subir_doc import Subir_DOC
from frontend.view.agregar_cliente_n import formulario_agregar_cliente_natural
from frontend.view.clientes import ClientesJuridicos, ClientesNaturales
from frontend.components.botones import boton_clientes
from frontend.view.agregar_empresa import formulario_agregar_empresa

#from frontend.components.botones import boton #para los botones de cada inicio de módulo, agregar, modificar, etc...

#Página de inicio 
def login():
    return Login()


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
                    boton_dos("plus", "/agregar_proveedor","Modificar proveedor"),
                    boton_dos("plus", "/agregar_proveedor","Listado proveedores")
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

#Página de agregar o subir socumentación 
def agregar_doc_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            Subir_DOC(),   
        ),
    )


#pagina de los clientes naturales
def clientes_page():
    return rx.vstack(
        navbar(),
        rx.hstack(  # Mantenemos los elementos en una fila
            Inicio(),
            rx.vstack(  # Los botones y la tabla se colocan verticalmente uno encima del otro
                # Botones para agregar, modificar y listar clientes
                rx.hstack(

                    boton_dos("plus", "/clientes/agregar_cliente_n", "Agregar Cliente"),
                    boton_dos("plus", "/agregar_cliente_n","Modificar Cliente"),
                    boton_dos("plus", "/agregar_cliente_n","Listado Cliente"),

                ),
                # Separador entre los botones y la tabla
                rx.divider(),
                # Contenedor flexible para la tabla
                rx.container(
                    ClientesJuridicos(),
                    ClientesNaturales(),
                    style={
                        "overflow-x": "auto",  # Agrega desplazamiento horizontal si es necesario
                        "width": "900px",  # Establece el ancho en 830px
                    }
                ),
            ),
        ),
    )

#Página de agregar Clientes
def agregar_cliente_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            formulario_agregar_cliente_natural(),   
        ),
    )

def agregar_cliente_empresa_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            formulario_agregar_empresa(),   
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
app.add_page(proveedores_page, route="/proveedores")
app.add_page(agregar_proveedor_page, route="/proveedores/agregar_proveedor") #Redirige al formulario para agregar un proveedor
app.add_page(agregar_doc_page, route="/proveedores/agregar_proveedor/subir_doc")
app.add_page(clientes_page, route="/clientes")
app.add_page(agregar_cliente_page, route="/clientes/agregar_cliente_n")
app.add_page(agregar_cliente_empresa_page, route="/clientes/agregar_empresa")


#404 error personalizado
# Define tu componente personalizado para la página 404
def custom_404_component():
    return rx.text("Lo sentimos, la página que estás buscando no se pudo encontrar.")

# Ahora, puedes llamar al método para definir tu página 404 personalizada
app.add_custom_404_page(
    component=custom_404_component, 
    title='404 - Página no encontrada', 
    image='mi_imagen_404.ico', 
    description='La página que estás buscando no existe.'
)
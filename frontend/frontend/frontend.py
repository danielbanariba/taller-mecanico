import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inventario import Inventario
from frontend.view.inicio import Inicio
from frontend.view.pantalla_dashboard import grafica_de_barras, grafica_lineal
from frontend.view.proveedores import Proveedores
from frontend.login import Login
#from frontend.view.agregar_proveedor_page import formulario_agregar_proveedor
#from frontend.components.botones import boton #para los botones de cada inicio de módulo, agregar, modificar, etc...


#Ejmplo para seguir haciendo mas directorios o direcciones. https://reflex.dev/docs/pages/routes/#getting-the-current-page-link

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
                    rx.button("Agregar proveedor", type="submit", margin_top="20px"),
                    rx.button("Modificar proveedor", type="submit", margin_top="20px"),
                    rx.button("Listado proveedores", type="submit", margin_top="20px")
                ),
                # Separador entre los botones y la tabla
                rx.divider(),
                # Contenedor flexible para la tabla
                rx.container(
                    Proveedores(),
                    style={
                        "overflow-x": "auto",  # Agrega desplazamiento horizontal si es necesario
                        "width": "1098px",  # Establece el ancho en 1098px
                    }
                ),
            ),
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
#app.add_page(agregar_proveedor_page, route="/agregar_proveedor")
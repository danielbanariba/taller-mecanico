import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inicio import Inicio
from frontend.view.agregar_cliente import code_setter
from frontend.login import Login
from frontend.view.agregar_empleado import formulario_agregar_empleado
from frontend.view.agregar_cotizacion import formulario_cotizacion
from frontend.view.error_404 import error_404
from frontend.user_page import UserState, user_page
from frontend.inventario_page import InventarioState, inventario_page
from frontend.pages.estadisticas import estadisticas
from frontend.pages.usuarios import usuarios
from frontend.pages.inventarios import inventarios
from frontend.pages.proveedores import proveedores_page, agregar_proveedor_page, modificar_proveedor_page, listado_proveedor_page, agregar_doc_page
from frontend.figures.calendar import calendar_page
from frontend.pages.cotizacion import agregar_cotizacion_page
from frontend.pages.clientes import agregar_cliente_page, clientes_page2
from frontend.pages.empleados import empleado_page

#Página de inicio 
def login():
    return Login()

#Página de inicio
def inicio_page():
    return rx.vstack(
        navbar(),
        Inicio(),   
    )

def inventarios():
    return rx.vstack(
        navbar(),
        rx.hstack(
            Inicio(),
            inventario_page()
        )
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
"""def modificar_empleado_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            detalles_empleado(),   
        ),
    )"""
#Página de agregar o subir socumentación 
"""def agregar_doc_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            Subir_DOC(),   
        ),
    )"""

"""def listado_empleado_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            #Inicio(),
            Empleados(),   
        ),
    )"""

# Crea la aplicación
app = rx.App()

#Genera las url o los directorios de la paginas correspondientes
app.add_page(login, route="/")
app.add_page(estadisticas, route="/estadisticas")
app.add_page(usuarios, route='/usuarios', title='usuarios', on_load=UserState.get_all_user)
#app.add_page(proveedores, route='/proveedor', title='proveedor', on_load=ProvedorState.get_all_provedor)
app.add_page(inventarios, route='/inventarios', title='inventarios', on_load=InventarioState.get_all_inventario)
app.add_page(inicio_page, route="/inicio")
app.add_page(agregar_empleado_page, route="/empleados/agregar_empleado") 
app.add_page(empleado_page, route="/empleados")
app.add_page(clientes_page2, route="/clientes2")
"""app.add_page(proveedores_page, route="/empleados")
app.add_page(agregar_empleado_page, route="/empleados/agregar_empleado") 
app.add_page(modificar_proveedor_page, route="/empleados/modificar_empleado") 
app.add_page(listado_proveedor_page, route="/empleados/listado_empleado") 
app.add_page(agregar_doc_page, route="/empleados/agregar_empleado/subir_doc")
app.add_page(agregar_doc_page, route="/empleados/agregar_empleado/subir_doc")"""
app.add_page(proveedores_page, route="/proveedores")
app.add_page(agregar_proveedor_page, route="/proveedores/agregar_proveedor") #Redirige al formulario para agregar un proveedor
app.add_page(modificar_proveedor_page, route="/proveedores/modificar_proveedor") 
app.add_page(listado_proveedor_page, route="/proveedores/listado_proveedor") 
app.add_page(agregar_doc_page, route="/proveedores/agregar_proveedor/subir_doc")
app.add_page(agregar_doc_page, route="/clientes/agregar_cliente/subir_doc") 
app.add_page(agregar_cliente_page, route="/clientes/agregar_cliente")
app.add_page(agregar_cotizacion_page, route="/cotizacion/agregar_cotizacion")
app.add_page(calendar_page, route="/agenda")


# Ahora, puedes llamar al método para definir tu página 404 personalizada
app.add_custom_404_page(
    component=error_404, 
    title='404 - Página no encontrada', 
    image='mi_imagen_404.ico', 
    description='La página que estás buscando no existe.'
)
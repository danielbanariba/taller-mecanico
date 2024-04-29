import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inventario import Inventario
from frontend.view.inicio import Inicio
from frontend.view.agregar_cliente import code_setter
#from frontend.view.empleados import Empleados
from frontend.view.proveedores import Proveedores
from frontend.login import Login
#from frontend.view.agregar_proveedor import formulario_agregar_empleado
#from frontend.view.modificar_proveedor import detalles_empleado
from frontend.view.error_404 import error_404
from frontend.user_page import UserState
from frontend.inventario_page import InventarioState
from frontend.proveedor_page import ProvedorState
from frontend.pages.estadisticas import estadisticas
from frontend.pages.clientes import clientes
from frontend.pages.inventarios import inventarios
from frontend.pages.proveedores import proveedores_page, agregar_proveedor_page, modificar_proveedor_page, listado_proveedor_page, agregar_doc_page


#Página de inicio 
def login():
    return Login()


#Página de ejemplo
def about():
    return rx.text("About Page")


#Página de inicio
def inicio_page():
    return rx.vstack(
        navbar(),
        Inicio(),   
    )

#Página de agregar proveedores
"""def agregar_empleado_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            formulario_agregar_empleado(),   
        ),
    )"""
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

#CLIENTES
#Página de agregar proveedores
def agregar_cliente_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            code_setter(),   
        ),
    )
# Crea la aplicación
app = rx.App()

#Genera las url o los directorios de la paginas correspondientes
app.add_page(login, route="/")
app.add_page(estadisticas, route="/estadisticas")
app.add_page(clientes, route='/clientes', title='clientes', on_load=UserState.get_all_user)
#app.add_page(proveedores, route='/proveedor', title='proveedor', on_load=ProvedorState.get_all_provedor)
app.add_page(inventarios, route='/inventarios', title='inventarios', on_load=InventarioState.get_all_inventario)
app.add_page(about)
"""app.add_page(proveedores_page, route="/empleados")
app.add_page(agregar_proveedor_page, route="/empleados/agregar_empleado") 
app.add_page(modificar_proveedor_page, route="/empleados/modificar_empleado") 
app.add_page(listado_proveedor_page, route="/empleados/listado_empleado") 
app.add_page(agregar_doc_page, route="/empleados/agregar_empleado/subir_doc")
app.add_page(agregar_doc_page, route="/empleados/agregar_empleado/subir_doc")"""
app.add_page(proveedores_page, route="/proveedores")
app.add_page(agregar_proveedor_page, route="/proveedores/agregar_proveedor") #Redirige al formulario para agregar un proveedor
app.add_page(modificar_proveedor_page, route="/proveedores/modificar_proveedor") 
app.add_page(listado_proveedor_page, route="/proveedores/listado_proveedor") 
app.add_page(agregar_doc_page, route="/proveedores/agregar_proveedor/subir_doc")
app.add_page(agregar_doc_page, route="/proveedores/agregar_proveedor/subir_doc") 
app.add_page(agregar_cliente_page, route="/clientes/agregar_cliente")

# Ahora, puedes llamar al método para definir tu página 404 personalizada
app.add_custom_404_page(
    component=error_404, 
    title='404 - Página no encontrada', 
    image='mi_imagen_404.ico', 
    description='La página que estás buscando no existe.'
)
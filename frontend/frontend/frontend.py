import reflex as rx
from frontend.view.navbar import navbar
from frontend.view.inventario import Inventario
from frontend.view.inicio import Inicio
from frontend.view.inicio_de_sesion import inicio_de_sesion

#Ejmplo para seguir haciendo mas directorios o direcciones. https://reflex.dev/docs/pages/routes/#getting-the-current-page-link

#Página de inicio 
def index():
    return inicio_de_sesion()

#Página de ejemplo
def about():
    return rx.text("About Page")

def inicio_page():
    return Inicio()

#Página de inventario
def inventario_page():
    return rx.vstack(#Combina los elementos en una columna vertical
        navbar(),
        rx.hstack(
            Inicio(),
            Inventario(),   
        ),
    )
    

app = rx.App()

#Genera las url o los directorios de la paginas correspondientes
app.add_page(index)
app.add_page(about)
app.add_page(inventario_page, route="/inventario")
app.add_page(inicio_page, route="/inicio")
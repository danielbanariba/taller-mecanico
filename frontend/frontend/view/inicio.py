import reflex as rx
from frontend.components.botones import boton
import frontend.URL as URL

def Inicio():
    return rx.vstack(
        boton("users-round", "/Clientes", "Clientes"),
        boton("notebook-text", "/Cotizacion/Factura", "Cotizacion/Factura"),
        boton("notebook-pen", "/Orden de servicio", "Orden de servicio"),
        boton("package-search", "/inventario", "Inventario"), #TODO investigar porque no abre la pagina
        boton("user-round-search", "/Empleados", "Empleados"),
        boton("scroll-text", "/Agenda", "Agenda"),
        boton("text-search", "/Informes", "Informes"),
        boton("factory", "/Proveedores", "Proveedores"),
        boton("settings", "/Configuracion", "Configuracion"),
        margin="20px"# Le da un espacio de 20px a todos los botones
    )
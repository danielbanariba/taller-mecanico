import reflex as rx
from frontend.components.botones import boton
import frontend.URL as URL

def Inicio():
    return rx.vstack(
        boton("user", "/usuarios", "Usuario"),
        boton("users-round", "/clientes2", "Clientes"),
        boton("notebook-text", "/cotizacion/agregar_cotizacion", "Cotizacion/Factura"),
        boton("notebook-pen", "/Orden de servicio", "Orden de servicio"),
        boton("package-search", "/inventarios", "Inventario"),
        boton("user-round-search", "/empleados", "Empleados"),
        boton("scroll-text", "/agenda", "Agenda"),
        boton("text-search", "/estadisticas", "Informes"),
        boton("factory", "/proveedores", "Proveedores"),
        #boton("settings", "/Configuracion", "Configuracion"),
        margin="20px"# Le da un espacio de 20px a todos los botones
    )
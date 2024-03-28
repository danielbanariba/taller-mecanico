import reflex as rx
from frontend.components.botones import boton

def inicio():
    return rx.vstack(
        boton("users-round", "/Clientes", "Clientes"),
        boton("notebook-text", "/Cotizacion/Factura", "Cotizacion/Factura"),
        boton("notebook-pen", "/Orden de servicio", "Orden de servicio"),
        boton("package-search", "/Inventario", "Inventario"),
        boton("user-round-search", "/Empleados", "Empleados"),
        boton("scroll-text", "/Agenda", "Agenda"),
        boton("text-search", "/Informes", "Informes"),
        boton("factory", "/Proveedores", "Proveedores"),
        boton("settings", "/Configuracion", "Configuracion"),
    )
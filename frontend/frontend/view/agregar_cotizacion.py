#COTIZACION
import reflex as rx
from reflex_dynoselect import dynoselect
import pandas as pd
from datetime import datetime, timedelta
from frontend.components.botones import boton_dos
from frontend.components.botones import boton_tres

# Clase para manejar el estado de cotizaciones
class EstadoCotizacion(rx.State):
    # Número de cotización por defecto
    no_cotizacion = 1000

    # Método de clase para obtener las fechas predeterminadas
    @classmethod
    def obtener_fechas(cls):
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        fecha_vencimiento = (datetime.now() + 7 * timedelta(days=1)).strftime("%Y-%m-%d")
        return fecha_actual, fecha_vencimiento


# Definición del formulario de cotización
def formulario_cotizacion():
    # Obtener las fechas desde el estado sin instanciar
    fecha_cotizacion, fecha_vencimiento = EstadoCotizacion.obtener_fechas()

    # Opciones para la marca y el color
    marcas_autos = ["Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "Hyundai"]
    colores = [
        {"value": "red", "label": "Rojo"},
        {"value": "blue", "label": "Azul"},
        {"value": "green", "label": "Verde"},
        {"value": "yellow", "label": "Amarillo"},
        {"value": "black", "label": "Negro"},
        {"value": "white", "label": "Blanco"},
    ]
    # Opciones para la selección de modelos. Puedes inicializarla vacía o con valores predeterminados
    modelos_autos = ["Modelo A", "Modelo B", "Modelo C"]
    return rx.container(
        rx.flex(
            rx.center(rx.text("Nueva cotización"), bg="lightblue"), 
            width="800px",
            margin_top="25px",
            margin_bottom="20px",
        ),
        # Sección de información básica del cliente
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text("Nombre del cliente"),
                    rx.input(placeholder="Nombre del cliente", style={"width": "400px"}),
                ),
                rx.vstack(
                    rx.text("No. Cotización"),
                    rx.input(
                        placeholder="No. Cotización",
                        value=str(EstadoCotizacion.no_cotizacion),
                        disabled=True,
                        style={"width": "400px"},
                    ),
                ),
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Fecha de cotización"),
                    rx.input(
                        placeholder="Fecha de cotización",
                        value=fecha_cotizacion,
                        disabled=True,
                        style={"width": "400px"},
                    ),
                ),
                rx.vstack(
                    rx.text("Fecha de vencimiento"),
                    rx.input(
                        placeholder="Fecha de vencimiento",
                        value=fecha_vencimiento,
                        disabled=True,
                        style={"width": "400px"},
                    ),
                ),
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Número de placa"),
                    rx.input(
                        placeholder="Número de placa",
                        style={"width": "400px"},
                    ),
                ),
                rx.vstack(
                    rx.text("Marca de auto"),
                    rx.select(
                        marcas_autos,
                        placeholder="Seleccionar marca",
                        style={"width": "400px"},
                    ),
                ),
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Motor"),
                    rx.input(
                        placeholder="Motor",
                        style={"width": "400px"},
                    ),
                ),
                rx.vstack(
                    rx.text("Modelo"),
                    rx.select(
                        items=modelos_autos,  # Agregar las opciones requeridas para el 'select'
                        placeholder="Seleccionar modelo",
                        style={"width": "400px"},
                    ),
                ),
            ),
            rx.vstack(
                rx.text("Color"),
                dynoselect(
                    options=colores,  # 
                    placeholder="Seleccionar color",
                    search_placeholder="Buscar color",
                ),
            ),
            rx.vstack(
                rx.text("Diagnóstico"),
                rx.input(
                    type="text",
                    placeholder="Diagnóstico",
                    multiline=True,
                    rows=3,
                    style={"width": "800px"},
                ),
            ),
        ),

        # Sección de tablas para mano de obra y repuestos
        rx.vstack(
            rx.text("Mano de Obra"),
            rx.data_table(
                data=pd.DataFrame(
                    columns=[
                        "ID Repuesto",
                        "Nombre de repuesto",
                        "Precio unitario",
                        "Precio Total"
                    ],
                ),
                pagination=True,  # El argumento 'pagination' debe ir aquí, no en el 'DataFrame'
                sort=True,
                search=True,
            ),
            rx.text("Repuestos"),
            rx.data_table(
                data=pd.DataFrame(
                    columns=["ID Repuesto", "Nombre de repuesto", "Precio unitario", "Precio Total"],
                   
                ),
                pagination=True,
                sort=True,
                search=True,
            ),
        ),

                # Botón de enviar
        rx.hstack(
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button("Guardar", color_scheme="purple"),
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Nueva cotización"),
                    rx.alert_dialog.description(
                        "Confirmar y guardar cotización.",
                    ),
                    rx.flex(
                        rx.alert_dialog.cancel(
                            rx.button("Cancelar"),
                            style={
                                    'width': '150px', 
                                    'height': '30px',
                                    'backgroundColor': '#b39eff',
                                    'cursor': 'pointer',  # Cambia el cursor a una mano
                                    'margin': '0',
                                    'fontSize': '15px',  # Ajusta el tamaño del texto aquí
                                    ':hover': {
                                        'backgroundColor': '#9f87de',  # Cambia el color de fondo cuando se pasa el cursor por encima
                                        'transition': '0.3s',
                                        },
                                },
                        ),
                        rx.alert_dialog.action(
                            boton_tres("check", "/cotizacion/agregar_cotizacion", "Confirmar"),
                        ),
                        spacing="3",
                    ),
                ),
            ),
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button("Imprimir", color_scheme="purple"),
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Imprimir la cotización."),
                    rx.alert_dialog.description(
                        "Imprimir.",
                    ),
                    rx.flex(
                        rx.alert_dialog.cancel(
                            rx.button("Cancelar"),
                            style={
                                    'width': '150px', 
                                    'height': '30px',
                                    'backgroundColor': '#b39eff',
                                    'cursor': 'pointer',  # Cambia el cursor a una mano
                                    'margin': '0',
                                    'fontSize': '15px',  # Ajusta el tamaño del texto aquí
                                    ':hover': {
                                        'backgroundColor': '#9f87de',  # Cambia el color de fondo cuando se pasa el cursor por encima
                                        'transition': '0.3s',
                                        },
                                },
                        ),
                        rx.alert_dialog.action(
                            boton_tres("check", "/cotizacion", "Confirmar"),
                        ),
                        spacing="3",
                    ),
                ),
            ),
            
        ),
    )

def agregar_cotizacion_page():
    return rx.container(
        formulario_cotizacion(),
    )
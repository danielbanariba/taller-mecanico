import reflex as rx
from .model.iventario_model import Inventario
from .service.inventario_service import select_all_inventario_service, select_inventario_by_id_service, create_inventario_service, delete_inventario_service
from .components.notify import notify_component
import asyncio
from .styles.styles import STYLE_NOTIFY

class InventarioState(rx.State):
    inventarios: list[Inventario]
    id_inventario_buscar: int
    error: str = ''

    @rx.background
    async def get_all_inventario(self):
        async with self:
            self.inventarios = select_all_inventario_service()

    @rx.background
    async def get_inventario_by_id(self):
        async with self:
            self.inventarios = select_inventario_by_id_service(self.id_inventario_buscar)

    async def handleNotify(self):
        async with self:
            await asyncio.sleep(4)
            self.error = ''

    @rx.background
    async def create_inventario(self, data: dict):
        async with self:
            try:
                self.inventarios = create_inventario_service(cantidad_productos=data['cantidad_productos'], fecha_entrada=data['fecha_entrada'], fecha_salida=data['fecha_salida'], id_repuesto=data['id_repuesto'])
            except BaseException as be:
                print(be.args)
                self.error = be.args
        await self.handleNotify()

    def id_inventario_on_change(self, value: int):
        self.id_inventario_buscar = value

    @rx.background
    async def delete_inventario_by_id(self, id_inventario):
        async with self:
            self.inventarios = delete_inventario_service(id_inventario)

@rx.page(route='/inventario', title='inventario', on_load=InventarioState.get_all_inventario)
def inventario_page() -> rx.Component:
    return rx.flex(
        rx.heading('Inventario', align='center'),
        rx.hstack(
            buscar_inventario_component(),
            create_inventario_dialogo_component(),
            justify='center',
            style={"margin-top": "30px"}
        ),
        table_inventario(InventarioState.inventarios),
        rx.cond(
            InventarioState.error != '',
            rx.callout(
                "You can't create an inventory that already exists",
                icon="alert_triangle",
                color_scheme="red",
                role="alert",
                style = STYLE_NOTIFY,
            ),
        ),
        direction='column',
        style={"width": "60vw", "margin": "auto"}
    )

def table_inventario(list_inventario: list[Inventario]) -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("ID"), 
                rx.table.column_header_cell("Cantidad de Productos"),
                rx.table.column_header_cell("Fecha de Entrada"),
                rx.table.column_header_cell("Fecha de Salida"),
                rx.table.column_header_cell("ID de Repuesto"),
                rx.table.column_header_cell("Accion"),
            ),
        ),
        rx.table.body(
            rx.foreach(list_inventario, row_table)
        ),
    )

def row_table(inventario: Inventario) -> rx.Component:
    return rx.table.row(
        rx.table.cell(str(inventario.id_inventario)),
        rx.table.cell(str(inventario.cantidad_productos)),
        rx.table.cell(inventario.fecha_entrada),
        rx.table.cell(inventario.fecha_salida),
        rx.table.cell(str(inventario.id_repuesto)),
        rx.table.cell(
            rx.hstack(
                delete_inventario_dialogo_component(inventario.id_inventario),
            ),
        ),
    )

def buscar_inventario_component() -> rx.Component:
    return rx.hstack(
        rx.input(placeholder="Ingrese el ID del inventario", type="number", on_change=InventarioState.id_inventario_on_change),
        rx.button("Buscar inventario", on_click=InventarioState.get_inventario_by_id)
    )

def create_inventario_form() -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.input(
                placeholder="Cantidad de Productos",
                name="cantidad_productos",
                type="number",
            ),
            rx.input(
                placeholder="Fecha de Entrada",
                            name="fecha_entrada",
                type="date",
            ),
            rx.input(
                placeholder="Fecha de Salida",
                name="fecha_salida",
                type="date",
            ),
            rx.input(
                placeholder="ID de Repuesto",
                name="id_repuesto",
                type="number",
            ),
            rx.dialog.close(
                rx.button('Guardar', type='submit')
            ),
        ),
        on_submit=InventarioState.create_inventario,
    )

def create_inventario_dialogo_component() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(rx.button("Crear inventario")),
        rx.dialog.content(
            rx.flex(
                rx.dialog.title("Crear inventario"),
                create_inventario_form(),
                justify='center',
                align='center',
                direction='column',
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button('Cancelar', color_scheme='gray', variant='soft')
                ),
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
            style={"width": "300px"}
        ),
    )

def delete_inventario_dialogo_component(id_inventario: int) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(rx.button(rx.icon("trash-2"))),
        rx.dialog.content(
            rx.dialog.title("Eliminar inventario"),
            rx.dialog.description("¿Estás seguro de que quieres eliminar el inventario con ID " + str(id_inventario) + "?"),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        'Cancelar', 
                        color_scheme='gray',
                        variant='soft'
                    ),
                ),
                rx.dialog.close(
                    rx.button(
                        'Confirmar', 
                        on_click=InventarioState.delete_inventario_by_id(id_inventario),
                    ),
                ),
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
        ),
    )

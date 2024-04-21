import reflex as rx
from .model.proveedor_model import Proveedor
from .service.proveedor_service import select_all

class ProvedorState(rx.State):
    #states
    proveedores:list[Proveedor]
    
    @rx.background
    async def get_all_provedor(self):
        async with self:
            self.proveedores = select_all()


@rx.page(route='/PROVEEDOR', title='PROVEEDOR', on_load=ProvedorState.get_all_provedor)
def proveedor_page() -> rx.Component:
    return rx.flex(
        rx.heading('Proveedores', align='center'),
        #rx.hstack(
            
        #),
        table_provedor(ProvedorState.proveedores),
        #TODO cambiar el estilo, para que sincronice con el estilo de cada componente
        direction='column',
        style={"width": "60vw", "margin": "auto"}
    )


def table_provedor(list_provedor: list[Proveedor]) -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("ID Proveedor"),
                rx.table.column_header_cell("Nombre Proveedor"),
                rx.table.column_header_cell("Direccion"),
                rx.table.column_header_cell("RTN"),
                rx.table.column_header_cell("Telefono"),
                rx.table.column_header_cell("Correo"),
                rx.table.column_header_cell("ID Vendedor"),
                rx.table.column_header_cell("DOC Adjunto"),
            ),
        ),
        rx.table.body(
            rx.foreach(list_provedor, row_table)# Recorre la lista de useres
        ),
    )


def row_table(PROVEEDOR: Proveedor) -> rx.Component:
    return rx.table.row(
        rx.table.cell(PROVEEDOR.id_proveedor),
        rx.table.cell(PROVEEDOR.nom_proveedor),
        rx.table.cell(PROVEEDOR.id_direccion),
        rx.table.cell(PROVEEDOR.rtn),
        rx.table.cell(PROVEEDOR.id_tel),
        rx.table.cell(PROVEEDOR.correo),
        rx.table.cell(PROVEEDOR.id_vendedor),
        rx.table.cell(PROVEEDOR.adj_doc),
        rx.table.cell(
            rx.hstack(
                rx.button('Eliminar'),
            ),
        ),
    )
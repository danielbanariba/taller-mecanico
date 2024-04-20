import reflex as rx
from .model.user_model import User
from .service.user_service import select_all

class UserState(rx.State):
    #states
    users:list[User]
    
    @rx.background
    async def get_all_user(self):
        async with self:
            self.users = select_all()


@rx.page(route='/user', title='Proovedor', on_load=UserState.get_all_user)
def user_page() -> rx.Component:
    return rx.flex(
        rx.heading('Usuarios', align='center'),
        #rx.hstack(
            
        #),
        table_user(UserState.users),
        #TODO cambiar el estilo, para que sincronice con el estilo de cada componente
        direction='column',
        style={"width": "60vw", "margin": "auto"}
    )


def table_user(list_user: list[User]) -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Nombre"), 
                rx.table.column_header_cell("Email"),
                rx.table.column_header_cell("Telefono"),
                rx.table.column_header_cell("Accion"),
            ),
        ),
        rx.table.body(
            rx.foreach(list_user, row_table)# Recorre la lista de useres
        ),
    )


def row_table(user: User) -> rx.Component:
    return rx.table.row(
        rx.table.cell(user.name),
        rx.table.cell(user.username),
        rx.table.cell(user.phone),
        rx.table.cell(
            rx.hstack(
                rx.button('Eliminar'),
            ),
        ),
    )
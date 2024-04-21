import reflex as rx
from .model.user_model import User
from .service.user_service import select_all_user_serice, selec_user_by_email_service

class UserState(rx.State):
    #states
    users:list[User]
    user_buscar: str
    
    @rx.background
    async def get_all_user(self):
        async with self:
            self.users = select_all_user_serice()

    @rx.background
    async def get_user_by_email(self):
        async with self:
            self.users = selec_user_by_email_service(self.user_buscar) 

    def buscar_on_change(self, value: str):
        self.user_buscar = value
        self.get_user_by_email()

@rx.page(route='/user', title='user', on_load=UserState.get_all_user)
def user_page() -> rx.Component:
    return rx.flex(
        rx.heading('Usuarios', align='center'),
        rx.hstack(
            buscar_user_component(),
            justify='center',
            style={"margin-top": "30px"}
        ),
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
    
    
def buscar_user_component() -> rx.Component:
    return rx.hstack(
        rx.input(placeholder="ingrese el email del usuario", on_change=UserState.buscar_on_change),
        rx.button("Buscar usuario", on_click=UserState.get_user_by_email)
    )
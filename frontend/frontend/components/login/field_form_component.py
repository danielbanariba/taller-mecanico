import reflex as rx

def field_form_component(label: str, placeholder: str, name_var:str, on_change_function, type_field:str):
    return rx.form.field(
        rx.flex(
            rx.form.label(label),
            rx.form.control(
                rx.input.input(
                    placeholder=placeholder,
                    on_change=on_change_function,
                    name=name_var,
                    type=type_field,
                    required=True
                ),
                as_child=True,
            ),
            rx.form.message(
                "El campo no puede ser nulo",
                match="valueMissing",
                color="red",
            ),
            direction="column",
            spacing="2",
            align="stretch",
        ),
        name=name_var,
        width="30vw"
    )
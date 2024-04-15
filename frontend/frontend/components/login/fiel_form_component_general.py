import reflex as rx

def fiel_form_component_general(label: str, placeholder: str, message_validate: str, name: str, on_change_function, show):
    return rx.form.field(
        rx.flex(
            rx.form.label(label),
            rx.form.control(
                rx.input.input(
                    placeholder=placeholder,
                    on_change=on_change_function,
                    name=name,
                    required=True
                ),
                as_child=True,
            ),
            rx.form.message(
                message_validate,
                name=name,
                match="valueMissing",
                force_math=show,
                color="red",
            ),
            direction="column",
            spacing="2",
            align="stretch",
        ),
        name=name,
        width="30vw",
    )
import reflex as rx

def form_user(label: str, placeholder: str, messege_validate: str, name: str, on_change_function, show) -> rx.Component:
    return rx.form.field(
                rx.flex(
                    rx.form.label(label),
                    rx.form.control(
                        rx.input.input(
                            placeholder=placeholder, 
                            on_change=on_change_function, 
                            name=name, 
                            required=True,
                        ),
                        as_child=True,
                        ),
                        rx.form.message(
                            messege_validate,
                            name=name,
                            match="valueMissing",
                            force_match=show,
                            color="red",
                        ),
                    direction="column",
                    spacing="2",
                    align="stretch",
                    ),
                    name=name,
                    width="30vw",
                )
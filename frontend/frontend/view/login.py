import re
import reflex as rx
import reflex.components.radix.primitives as rdxp
import frontend.styles.styles as styles

class RadixFormState(rx.State):
    # These track the user input real time for validation
    user_entered_password: str
    user_entered_email: str

    # These are the submitted data
    password: str
    email: str

    mock_password_db: list[str] = ["reflex", "admin"]

    @rx.var
    def invalid_email(self) -> bool:
        return not re.match(
            r"[^@]+@[^@]+.[^@]+", self.user_entered_email
        )

    @rx.var
    def password_empty(self) -> bool:
        return not self.user_entered_password.strip()

    @rx.var
    def password_is_taken(self) -> bool:
        return (
            self.user_entered_password
            in self.mock_password_db
        )

    @rx.var
    def input_invalid(self) -> bool:
        return (
            self.invalid_email
            or self.password_is_taken
            or self.password_empty
        )

    def handle_submit(self, form_data: dict):
        """Handle the form submit."""
        self.password = form_data.get("password")
        self.email = form_data.get("email")


def Login():
    return rx.box(
    rx.flex(
        rx.form.root(
            rx.flex(
                rx.form.field(
                    rx.flex(
                        rx.form.label("Email"),
                        rx.form.control(
                            rx.input.input(
                                placeholder="Correo electrónico",
                                on_change=RadixFormState.set_user_entered_email,
                                name="email",
                            ),
                            as_child=True,
                        ),
                        rx.form.message(
                            "Ingresa un correo válido",
                            match="valueMissing",
                            force_match=RadixFormState.invalid_email,
                            color="var(--red-11)",
                        ),
                        direction="column",
                        spacing="2",
                        align="stretch",
                    ),
                    name="email",
                    server_invalid=RadixFormState.invalid_email,
                ),
                rx.form.field(
                    rx.flex(
                        rx.form.label("password"),
                        rx.form.control(
                            rx.input.input(
                                placeholder="password",
                                # workaround: `name` seems to be required when on_change is set
                                on_change=RadixFormState.set_user_entered_password,
                                name="password",
                            ),
                            as_child=True,
                        ),
                        # server side validation message can be displayed inside a rx.cond
                        rx.cond(
                            RadixFormState.password_empty,
                            rx.form.message(
                                "password cannot be empty",
                                color="var(--red-11)",
                            ),
                        ),
                        # server side validation message can be displayed by `force_match` prop
                        rx.form.message(
                            "password already taken",
                            # this is a workaround:
                            # `force_match` does not work without `match`
                            # This case does not want client side validation
                            # and intentionally not set `required` on the input
                            # so "valueMissing" is always false
                            match="valueMissing",
                            force_match=RadixFormState.password_is_taken,
                            color="var(--red-11)",
                        ),
                        direction="column",
                        spacing="2",
                        align="stretch",
                    ),
                    name="password",
                    server_invalid=RadixFormState.password_is_taken,
                ),
                rx.form.submit(
                    rx.button(
                        "Submit",
                        disabled=RadixFormState.input_invalid,
                    ),
                    as_child=True,
                ),
                direction="column",
                spacing="4",
                width="25em",
            ),
            on_submit=RadixFormState.handle_submit,
            reset_on_submit=True,
        ),
        rx.divider(size="4"),
        rx.text(
            "password submitted: ",
            rx.text(
                RadixFormState.password,
                weight="bold",
                color="var(--accent-11)",
            ),
        ),
        rx.text(
            "Email submitted: ",
            rx.text(
                RadixFormState.email,
                weight="bold",
                color="var(--accent-11)",
            ),
        ),
        direction="column",
        spacing="4",
    ),
    style=styles.CENTRAR_LOGIN,
    )
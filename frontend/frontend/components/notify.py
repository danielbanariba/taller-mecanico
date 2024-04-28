# ESTO ES UN COMPONENTE!
import reflex as rx
from frontend.styles.styles import STYLE_NOTIFY

def notify_component(message: str, icon_notify: str, color: str) -> rx.Component:
    return rx.callout(
        message,
        icon=icon_notify,
        color_scheme=color,
        style=STYLE_NOTIFY,
    ),
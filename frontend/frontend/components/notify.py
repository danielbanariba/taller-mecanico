# ESTO ES UN COMPONENTE!
import reflex as rx

def notify_component(message: str, icon_notify: str, color: str) -> rx.Component:
    return rx.callout(
        message,
        icon=icon_notify,
        color_scheme=color,
        style=style_notify,
    ),

style_notify = {
    'position': 'fixed',
    'top': '0',
    'right': '0',
    'margin': '10px 10px',
}
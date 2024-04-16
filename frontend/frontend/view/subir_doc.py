import reflex as rx

#Pagina para la subida de documentación 
class State(rx.State):
    """The app state."""

    # The images to show.
    img: list[str]

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle the upload of file(s).

        Args:
            files: The uploaded files.
        """
        for file in files:
            upload_data = await file.read()
            outfile = rx.get_upload_dir() / file.filename

            # Save the file.
            with outfile.open("wb") as file_object:
                file_object.write(upload_data)

            # Update the img var.
            self.img.append(file.filename)


color = "rgb(107,99,246)"


def Subir_DOC():
    """The main view."""
    return rx.vstack(
        rx.upload(
            rx.vstack(
                rx.button("Select File", color=color, bg="white", border=f"1px solid {color}"),
                rx.text("Drag and drop files here or click to select files"),
            ),
            id="upload1",
            border=f"1px dotted {color}",
            padding="5em",
        ),
        rx.hstack(rx.foreach(rx.selected_files("upload1"), rx.text)),
        rx.button(
            "Upload",
            on_click=State.handle_upload(rx.upload_files(upload_id="upload1")),
        ),
        rx.button(
            "Clear",
            on_click=rx.clear_selected_files("upload1"),
        ),
        rx.foreach(State.img, lambda img: rx.image(src=rx.get_upload_url(img))),
        padding="5em",
    )


def agregar_doc_page(): 
    return rx.container(
        Subir_DOC(),
    )



import reflex as rx

class UploadExample(rx.State):
    uploading: bool = False
    progress: int = 0
    total_bytes: int = 0

    async def handle_upload(
        self, files: list[rx.UploadFile]
    ):
        for file in files:
            self.total_bytes += len(await file.read())

    def handle_upload_progress(self, progress: dict):
        self.uploading = True
        self.progress = round(progress["progress"] * 100)
        if self.progress >= 100:
            self.uploading = False

    def cancel_upload(self):
        self.uploading = False
        return rx.cancel_upload("upload3")

def Subir_DOC():
    return rx.vstack(
        rx.upload(
            rx.text(
                "Arrastre y suelte archivos aquí o haga clic para seleccionar archivos."
            ),
            id="upload3",
            border="1px dotted rgb(107,99,246)",
            padding="5em",
            margin_top="25px",
        ),
        rx.vstack(
            rx.foreach(
                rx.selected_files("upload3"), rx.text
            )
        ),
        rx.progress(value=UploadExample.progress, max=100),
        rx.cond(
            ~UploadExample.uploading,
            rx.button(
                "Cargar",color_scheme="purple", ###########
                on_click=UploadExample.handle_upload(
                    rx.upload_files(
                        upload_id="upload3",
                        on_upload_progress=UploadExample.handle_upload_progress,
                    ),
                ),
            ),
            rx.button(
                "Cancelar",
                on_click=UploadExample.cancel_upload,
            ),
        ),
        rx.text(
            "Total de bytes cargados: ",
            UploadExample.total_bytes,
        ),
        align="center",
    )
   
   
def agregar_doc_page(): 
    return rx.container(
        Subir_DOC(),
    )



from typing import Any

class Display:
    display: bool = False
    gradio_mode: bool = False
    image_display: Any = None

    def set_display(self, display: bool):
        self.display = display

    def set_gradio_mode(self, gradio_mode: bool, image_display: Any):
        self.gradio_mode = gradio_mode
        self.image_display = image_display
from typing import Any


class Display:
    display: bool = False
    gradio_mode: bool = False
    image_display: Any = None
    objective: Any = None
    url_input: Any = None
    instructions_history: Any = None
    history: Any = None

    def set_display(self, display: bool):
        self.display = display

    def set_gradio_mode(
        self,
        gradio_mode: bool,
        objective,
        url_input,
        image_display,
        instructions_history,
        history,
    ):
        self.gradio_mode = gradio_mode
        self.image_display = image_display
        self.objective = objective
        self.url_input = url_input
        self.instructions_history = instructions_history
        self.history = history

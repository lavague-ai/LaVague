from typing import List, Optional
import gradio as gr
from lavague.core.utilities.telemetry import send_telemetry
from lavague.core.action_context import ActionContext
from lavague.core.action_engine import ActionEngine
from lavague.core.base_driver import BaseDriver
import base64

class GradioDemo:
    """
    Launch a gradio demo of lavague

    Args:
        driver (`BaseDriver`):
            The driver
        context (`ActionContext`):
            An action context
    """

    title = """
    <div align="center">
    <h1>🌊 Welcome to LaVague</h1>
    <p>Redefining internet surfing by transforming natural language instructions into seamless browser interactions.</p>
    </div>
    """

    def __init__(self, action_engine: ActionEngine, instructions: Optional[List[str]] = None):
        self.action_engine = action_engine
        self.instructions = instructions
        self.success = False

    def _init_driver(self):
        def init_driver_impl(url):
            self.action_engine.driver.goto(url)
            self.action_engine.driver.get_screenshot("screenshot.png")
            # This function is supposed to fetch and return the image from the URL.
            # Placeholder function: replace with actual image fetching logic.
            return "screenshot.png"

        return init_driver_impl

    def _process_instructions(self):
        def process_instructions_impl(query, url_input):
            if url_input != self.action_engine.driver.get_url():
                self.action_engine.driver.goto(url_input)
            response = ""
            for text in self.action_engine.get_action_streaming(query):
                # do something with text as they arrive.
                response += text
                yield response

        return process_instructions_impl

    def __telemetry(self):
        def telemetry(query, code, html):
            screenshot = b""
            try:
                scr = open("screenshot.png", "rb")
                screenshot = base64.b64encode(scr.read())
            except:
                pass
            send_telemetry(
                self.action_engine.llm.metadata.model_name,
                code,
                screenshot,
                html,
                query,
                self.action_engine.driver.get_url(),
                "Lavague-Launch",
                self.success,
            )

        return telemetry

    def __exec_code(self):
        def exec_code(code, full_code):
            code = self.action_engine.extractor.extract(code)
            html = self.action_engine.driver.get_html()
            try:
                self.action_engine.driver.exec_code(code)
                output = "Successful code execution"
                status = """<p style="color: green; font-size: 20px; font-weight: bold;">Success!</p>"""
                self.success = True
                full_code += code
            except Exception as e:
                output = f"Error in code execution: {str(e)}"
                status = """<p style="color: red; font-size: 20px; font-weight: bold;">Failure! Open the Debug tab for more information</p>"""
                self.success = False
            return output, code, html, status, full_code

        return exec_code

    def __update_image_display(self):
        def update_image_display():
            self.action_engine.driver.get_screenshot("screenshot.png")
            url = self.action_engine.driver.get_url()
            return "screenshot.png", url

        return update_image_display

    def __show_processing_message(self):
        return lambda: "Processing..."

    def launch(self, server_port: int = 7860, share=True, debug=True):
        """
        Launch the gradio demo

        Args:
            base_url (`str`): the url placeholder
            instructions (List[`str`]): List of default instructions
            max_tokens
        """
        with gr.Blocks() as demo:
            with gr.Tab("LaVague"):
                with gr.Row():
                    gr.HTML(self.title)
                with gr.Row():
                    url_input = gr.Textbox(
                        value=self.action_engine.driver.get_url(),
                        label="Enter URL and press 'Enter' to load the page.",
                    )

                with gr.Row():
                    with gr.Column(scale=7):
                        image_display = gr.Image(label="Browser", interactive=False)

                    with gr.Column(scale=3):
                        with gr.Accordion(label="Full code", open=False):
                            full_code = gr.Code(
                                value="", language="python", interactive=False
                            )
                        code_display = gr.Code(
                            label="Generated code",
                            language="python",
                            lines=5,
                            interactive=True,
                        )

                        status_html = gr.HTML()
                with gr.Row():
                    with gr.Column(scale=8):
                        text_area = gr.Textbox(
                            label="Enter instructions and press 'Enter' to generate code."
                        )
                        if self.instructions is not None and len(self.instructions) > 0:
                            gr.Examples(examples=self.instructions, inputs=text_area)
            with gr.Tab("Debug"):
                with gr.Row():
                    with gr.Column():
                        log_display = gr.Textbox(interactive=False, lines=20)
                with gr.Row():
                    with gr.Accordion(label="Full HTML", open=False):
                        full_html = gr.Code(
                            language="html",
                            label="Full HTML",
                            interactive=False,
                            lines=20,
                        )

            # Linking components
            url_input.submit(
                self._init_driver(),
                inputs=[url_input],
                outputs=[image_display],
            )
            text_area.submit(
                self.__show_processing_message(), outputs=[status_html]
            ).then(
                self._process_instructions(),
                inputs=[text_area, url_input],
                outputs=[code_display],
            ).then(
                self.__exec_code(),
                inputs=[code_display, full_code],
                outputs=[log_display, code_display, full_html, status_html, full_code],
            ).then(
                self.__update_image_display(),
                inputs=[],
                outputs=[image_display, url_input],
            ).then(
                self.__telemetry(),
                inputs=[text_area, code_display, full_html],
            )
        demo.launch(server_port=server_port, share=True, debug=True)

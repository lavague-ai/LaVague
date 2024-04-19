from typing import Optional, List
from abc import ABC, abstractmethod
import gradio as gr
from selenium.webdriver.common.by import By  # import used by generated selenium code
from selenium.webdriver.common.keys import (
    Keys,
)
from .llm_models import OpenAILLM, AzureOpenAILLM, HuggingFaceLLM, OpenAILiteLLM, GroqApiLLM, AnthropicApiLLM
from .telemetry import send_telemetry
from .action_engine import BaseActionEngine, ActionEngine
from .driver import AbstractDriver
import base64

LLM_MODELS = {
    "OpenAI GPT-3.5": OpenAILLM,
    "HuggingFace Mixtral-8x7B": HuggingFaceLLM,
    "OpenAI LiteLLM-GPT-3.5-Turbo": OpenAILiteLLM,
    "OpenAI GPT-4 (AZURE)": AzureOpenAILLM,
    "Groq Mixtral-8x7B": GroqApiLLM,
    "Anthropic claude-3-haiku": AnthropicApiLLM
}

class CommandCenter(ABC):
    @abstractmethod
    def init_driver():
        pass

    @abstractmethod
    def process_instructions():
        pass


class GradioDemo(CommandCenter):
    """
    CommandCenter allows you to launch a gradio demo powered by selenium and the ActionEngine

    Args:
        actionEngine (`BaseActionEngine`):
            The action engine, with streaming enabled
        driver (`AbstractDriver`):
            The driver
    """

    title = """
    <div align="center">
    <h1>🌊 Welcome to LaVague</h1>
    <p>Redefining internet surfing by transforming natural language instructions into seamless browser interactions.</p>
    </div>
    """

    def __init__(self, actionEngine: BaseActionEngine, driver: AbstractDriver):
        self.actionEngine = actionEngine
        self.driver = driver
        self.base_url = ""
        self.success = False
        self.input_model_name = None

    def init_driver(self):
        def init_driver_impl(url):
            self.driver.goTo(url)
            self.driver.getScreenshot("screenshot.png")
            # This function is supposed to fetch and return the image from the URL.
            # Placeholder function: replace with actual image fetching logic.
            return "screenshot.png"

        return init_driver_impl

    def process_instructions(self):
        def process_instructions_impl(query, url_input):
            if url_input != self.driver.getUrl():
                self.driver.goTo(url_input)
            state = self.driver.getHtml()
            response = ""
            for text in self.actionEngine.get_action_streaming(query, state):
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
                self.actionEngine.llm.metadata.model_name,
                code,
                screenshot,
                html,
                query,
                self.driver.getUrl(),
                "Lavague-Launch",
                self.success,
            )

        return telemetry

    def __exec_code(self):
        def exec_code(code, full_code):
            code = self.actionEngine.cleaning_function(code)
            html = self.driver.getHtml()
            _, driver = self.driver.getDriver()  # define driver for exec
            try:
                exec(code)
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
            self.driver.getScreenshot("screenshot.png")
            url = self.driver.getUrl()
            return "screenshot.png", url

        return update_image_display

    def __show_processing_message(self):
        return lambda: "Processing..."

    def __set_action_engine(self, actionEngine: ActionEngine):
        """
        Set a new ActionEngine object.

        Args:
            actionEngine (`ActionEngine`): The new action engine to set.
        """
        self.actionEngine = actionEngine

    def __on_model_change(self,  model_name):
        llm_class = LLM_MODELS.get(model_name, None)
        if llm_class:
            action_engine = ActionEngine(llm_class(), self.actionEngine.embedder, self.actionEngine.prompt_template, self.actionEngine.cleaning_function)
            self.__set_action_engine(action_engine)
        else:
            raise ValueError(f"Unknown model: {model_name}")

    def set_input_model_name(self, input_model_name: str):
        self.input_model_name = input_model_name

    def run(self, base_url: str, instructions: List[str], server_port: int = 7860):
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
                        value=base_url,
                        label="Enter URL and press 'Enter' to load the page.",
                    )

                with gr.Row():
                    with gr.Column(scale=7):
                        image_display = gr.Image(label="Browser", interactive=False)

                    with gr.Column(scale=3):
                        with gr.Column(scale=3):
                            if self.input_model_name is None:
                                model_options = LLM_MODELS.keys()
                                initial_model = "OpenAI GPT-3.5"

                                model_dropdown = gr.Dropdown(model_options, value=initial_model, label="Model")
                                model_dropdown.change(self.__on_model_change, inputs=model_dropdown, outputs=None)
                            else:
                                model_input = gr.Textbox(
                                    label="Model",
                                    value=self.input_model_name,
                                    interactive=False
                                )

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
                        gr.Examples(examples=instructions, inputs=text_area)
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
                self.init_driver(),
                inputs=[url_input],
                outputs=[image_display],
            )
            text_area.submit(
                self.__show_processing_message(), outputs=[status_html]
            ).then(
                self.process_instructions(),
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

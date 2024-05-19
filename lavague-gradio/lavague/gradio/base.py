from typing import List, Optional
import gradio as gr
from lavague.core.utilities.telemetry import send_telemetry
from lavague.core import Context
from lavague.core import ActionEngine, WorldModel
from lavague.core.base_driver import BaseDriver
from lavague.core.utilities.web_utils import encode_image
from lavague.core.utilities.format_utils import extract_instruction
import time
import uuid
from PIL import Image

import base64

from lavague.drivers.selenium.base import SeleniumDriver

css_or = """
h1 {
    text-align: center;
    display:block;
}
"""

css = """body {
    font-family: Arial, sans-serif; /* Sets the font for the page */
    background-color: #1a1a1a; /* Dark background for the page */
    color: #fff; /* White text color */
    margin: 0;
    padding: 0;
}

.list-container {
    width: 300px; /* Set the width of the container */
    background: #333; /* Darker background for the list */
    border-radius: 8px; /* Rounded corners */
    box-shadow: 0 4px 8px rgba(0,0,0,0.3); /* Subtle shadow */
    margin: 20px auto; /* Centering the list */
    padding: 10px; /* Padding around the list */
}

ul {
    list-style: none; /* Removes default bullet points */
    padding: 0; /* Removes default padding */
    margin: 0; /* Removes default margin */
}

li {
    padding: 10px; /* Padding inside each list item */
    border-bottom: 1px solid #444; /* Separator between items */
    cursor: pointer; /* Pointer cursor on hover */
}

li:last-child {
    border-bottom: none; /* Removes border from the last item */
}
"""

html = """
<div class="list-container">
    <ul>
    </ul>
</div>
"""

class GradioAgentDemo:
    """
    Launch an agent gradio demo of lavague

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

    centered_text = """
    <div align="center">
    <h3>or</h3>
    </div>
    """


    def __init__(
        self, action_engine: ActionEngine, world_model: WorldModel, n_attempts: int = 5, n_steps: int = 5):
        self.action_engine = action_engine
        self.driver: SeleniumDriver = self.action_engine.driver
        self.world_model = world_model
        self.success = False
        self.n_attemps = n_attempts
        self.n_steps = n_steps

    def _init_driver(self):
        def init_driver_impl(url):
            self.action_engine.driver.goto(url)
            self.action_engine.driver.save_screenshot("screenshot.png")
            # This function is supposed to fetch and return the image from the URL.
            # Placeholder function: replace with actual image fetching logic.
            return "screenshot.png"

        return init_driver_impl

    def _process_instructions(self):

        def add_instruction(instruction, instructions_history):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(instructions_history, 'html.parser')
            new_item = soup.new_tag("li")
            new_item.string = instruction
            soup.find('ul').append(new_item)
                        
            items = soup.find_all('li')
            for item in items:
                item.attrs.pop('style', None)
                        
            items[-1]['style'] = "background-color: #555;"

            output = soup.prettify()
            return output
    
        def process_instructions_impl(objective, url_input, image_display, code_display, log_display, full_html, status_html, instructions_history):
            from selenium.webdriver.remote.webdriver import WebDriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys

            driver: WebDriver = self.action_engine.driver.get_driver()
            action_engine: ActionEngine = self.action_engine
            world_model: WorldModel = self.world_model
            driver.get(url_input)
            self.success = True
            error = ""
            url = ""
            image = None
            screenshot_after_action = None
            run_id = str(uuid.uuid4())
            process_success = False

            for i in range(self.n_steps):
                step_id = str(uuid.uuid4())
                self.success = True
                error = ""
                bounding_box = {"": 0}
                viewport_size = {"": 0}
                driver.save_screenshot("screenshot_before_action.png")
                screenshot_before_action = Image.open("screenshot_before_action.png")
                image_display = "screenshot_before_action.png"
                status_html = "Computing an action plan..."
                state = encode_image("screenshot_before_action.png")
                code_display = "# Loading..."
                yield url_input, image_display, code_display, log_display, full_html, status_html, instructions_history

                output = world_model.get_instruction(state, objective)
                instruction = extract_instruction(output)
                code_display = output
                status_html = "Action plan computed. Transforming the action into code..."
                yield url_input, image_display, code_display, log_display, full_html, status_html, instructions_history
                if instruction != "STOP":
                    print("Instruction received")
                    query = instruction
                    nodes = action_engine.get_nodes(query)
                    context = "\n".join(nodes)
                    for _ in range(self.n_steps):
                        try:
                            image = None
                            screenshot_after_action = None
                            error = ""
                            action = action_engine.get_action_from_context(context, query)
                            outputs = self.driver.get_highlighted_element(action)
                            image = outputs[-1]["image"]
                            bounding_box = outputs[-1]["bounding_box"]
                            viewport_size = outputs[-1]["viewport_size"]

                            image_display = image
                            status_html = "Action transformed into code. Showing the next element to interact with..."
                            yield url_input, image_display, code_display, log_display, full_html, status_html, instructions_history

                            time.sleep(3)

                            local_scope = {"driver": driver}

                            code = f"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
{action}""".strip()

                            exec(code, globals(), local_scope)
                            time.sleep(3)
                            driver.save_screenshot("screenshot_after_action.png")
                            screenshot_after_action = Image.open(
                                "screenshot_after_action.png"
                            )

                            url_input = driver.current_url

                            image_display = "screenshot_after_action.png"
                            status_html = "Instruction successfully executed"
                            yield url_input, image_display, code_display, log_display, full_html, status_html, instructions_history

                            break

                        except Exception as e:
                            success = False
                            error = repr(e)
                            status_html = "Action execution failed. Retrying..."
                            log_display = error
                            yield url_input, image_display, code_display, log_display, full_html, status_html, instructions_history
                            screenshot_after_action = None
                            image = None
                            pass
                else:
                    process_success = True
                    break
                instructions_history = add_instruction(instruction, instructions_history)
                yield url_input, image_display, code_display, log_display, full_html, status_html, instructions_history

            # instructions_history = add_instruction(url_input, instructions_history)
            if process_success:
                status_html = """<p style="color: green; font-size: 20px; font-weight: bold;">Success!</p>"""
            else:
                status_html = """<p style="color: red; font-size: 20px; font-weight: bold;">Failure, please try again.</p>"""
            yield url_input, image_display, code_display, log_display, full_html, status_html, instructions_history
            
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
                        value="https://huggingface.co/docs",
                        label="Enter URL and press 'Enter' to load the page.",
                    )

                with gr.Row():
                    with gr.Column(scale=7):
                        image_display = gr.Image(label="Browser", interactive=False)

                    with gr.Column(scale=3):

                        # with gr.Row():
                            # previous = gr.Button(value="Previous")
                            # next = gr.Button(value="Next")
                        code_display = gr.Code(
                            label="Chain of thoughts",
                            lines=5,
                            interactive=True,
                        )

                        status_html = gr.HTML()
                    
                        instructions_history = gr.HTML(html)

                with gr.Row():
                    with gr.Column(scale=4):
                        text_area = gr.Textbox(
                            label="Enter the objective and press 'Enter' to start processing it.",
                            value="Go on the quicktour of PEFT"
                        )
                        gr.HTML(self.centered_text)
                        text_area_instruction = gr.Textbox(
                            label="Enter yout instruction and press 'Enter' to start processing it.",
                            value=""
                        )

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
                            render=False,
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
                inputs=[text_area, url_input, image_display, code_display, log_display, full_html, status_html, instructions_history],
                outputs=[url_input, image_display, code_display, log_display, full_html, status_html, instructions_history],
            )
        demo.launch(server_port=server_port, share=True, debug=True)



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

    def __init__(
        self, action_engine: ActionEngine, instructions: Optional[List[str]] = None
    ):
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

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

html = """
<div class="list-container">
    <ul>
    </ul>
</div>
"""

css = """
    .my-button {
        max-height: 3rem !important;
        max-width: 5rem !important;
        min-width: min(100px,100%) !important;
}
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
    <div class='parent' align="center">
    <div class='child' style="display: inline-block !important;">
    <img src="https://raw.githubusercontent.com/lavague-ai/LaVague/new_gradio/docs/assets/logo.png" width=40px/>
    </div>
    <div class='child' style="display: inline-block !important;">
    <h1>LaVague</h1>
    </div>
    </div>
    """

    title_history = """
    <div align="center">
    <h3>Steps</h3>
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
    
        def process_instructions_impl(objective, url_input, image_display, instructions_history, history):
            from selenium.webdriver.remote.webdriver import WebDriver
            
            history[-1][1] = "..."

            driver: WebDriver = self.action_engine.driver.get_driver()
            action_engine: ActionEngine = self.action_engine
            world_model: WorldModel = self.world_model
            driver.get(url_input)
            self.success = True
            image = None

            for i in range(self.n_steps):
                self.success = True
                driver.save_screenshot("screenshot_before_action.png")
                image_display = "screenshot_before_action.png"
                state = encode_image("screenshot_before_action.png")
                yield objective, url_input, image_display, instructions_history, history

                output = world_model.get_instruction(state, objective)
                instruction = extract_instruction(output)
                # Too long to print out all the thoughts unless for debug imo
                # history[-1][1] = output
                history[-1][1] = f"Step #{i + 1}: {instruction}"
                yield objective, url_input, image_display, instructions_history, history
                if instruction != "STOP":
                    html = driver.page_source
                    nodes = action_engine.get_nodes(instruction)
                    context = "\n".join(nodes)
                    for x in range(self.n_steps):
                        try:
                            history[-1][1] = "⏳ ..."
                            image = None
                            action = action_engine.get_action_from_context(context, instruction)
                            outputs = self.driver.get_highlighted_element(action)
                            image = outputs[-1]["image"]
                            image_display = image
                            yield objective, url_input, image_display, instructions_history, history

                            time.sleep(1)

                            local_scope = {"driver": driver}

                            code = f"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
{action}""".strip()

                            exec(code, globals(), local_scope)
                            driver.save_screenshot("screenshot_after_action.png")
                            url_input = driver.current_url

                            image_display = "screenshot_after_action.png"
                            yield objective, url_input, image_display, instructions_history, history

                            break

                        except Exception as e:
                            history[-1][1] = f"⏳ Error occurred, trying again..."
                            print(e)
                            yield objective, url_input, image_display, instructions_history, history
                            image = None
                            pass
                else:
                    break
                yield objective, url_input, image_display, instructions_history, history

            history[-1][1] = "✅ Done."
            yield objective, url_input, image_display, instructions_history, history
            
        return process_instructions_impl
    
    def __add_message(self):
        def clear_instructions(instruction, instructions_history):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(instructions_history, 'html.parser')
            soup.find('ul').clear()

            output = soup.prettify()
            return output
        
        def add_message(history, message, instructions_history):
            instructions_history = clear_instructions("", instructions_history)
            history.append((message, None))
            return history, instructions_history
        
        return add_message

    def launch(self, server_port=7860, share=True, debug=True):
        def toggle_to_url():
            return (
                gr.update(visible=True), 
                gr.update(visible=False),
                gr.update(elem_classes=["selected", "my-button"]),
                gr.update(elem_classes=["unselected", "my-button"])
            )

        def toggle_to_objective():
            return (
                gr.update(visible=False), 
                gr.update(visible=True),
                gr.update(elem_classes=["unselected", "my-button"]),
                gr.update(elem_classes=["selected", "my-button"])
            )

        with gr.Blocks(gr.themes.Default(primary_hue="blue", secondary_hue="neutral"), css=css) as demo:
            with gr.Tab("LaVague"):
                with gr.Row():
                    gr.HTML(self.title)

                with gr.Row(equal_height=False):
                    with gr.Column():
                        with gr.Row():
                                url_button = gr.Button("URL", scale=0, variant="primary", elem_classes=["selected", "my-button"],)
                                objective_button = gr.Button("Objective", scale=0, variant="secondary", elem_classes=["unselected", "my-button"])
                                url_input = gr.Textbox(
                                value="",
                                scale=9,
                                type="text",
                                label="Enter URL and press 'Enter' to load the page.",
                                visible=True
                                )
                                objective_input = gr.Textbox(
                                    value="",
                                    scale=9,
                                    type="text",
                                    label="Enter the objective and press 'Enter' to start processing it.",
                                    visible=False
                                )
                with gr.Row(variant="panel", equal_height=True):
                    with gr.Column(scale=7):
                        image_display = gr.Image(label="Browser", interactive=False,  height="70%")
                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(
                            [],
                            elem_id="chatbot",
                            bubble_full_width=True,
                            height="70%",
                            placeholder="Agent output will be shown here\n",
                            layout="bubble"
                        )
                        instructions_history = gr.HTML("<div class='list-container'><ul></ul></div>")
                url_button.click(toggle_to_url, [], [url_input, objective_input, url_button, objective_button])
                objective_button.click(toggle_to_objective, [], [url_input, objective_input, url_button, objective_button])
                
                # objective submission handling
                objective_input.submit(self.__add_message(), inputs=[chatbot, objective_input, instructions_history], outputs=[chatbot, instructions_history]).then(
                self._process_instructions(),
                inputs=[objective_input, url_input, image_display, instructions_history, chatbot],
                outputs=[objective_input, url_input, image_display, instructions_history, chatbot],
            )
                # submission handling
                url_input.submit(self._init_driver(), inputs=[url_input], outputs=[image_display])
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
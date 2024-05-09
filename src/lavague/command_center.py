from typing import Optional, List
from abc import ABC, abstractmethod
import gradio as gr

from .telemetry import send_telemetry
from .action_engine import ActionEngine
from .driver import AbstractDriver
import base64


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

def append_value(values):
    print(values)
    import numpy as np
    
    value = str(np.random.randint(0,1024))
    values.append(value)
    update = gr.CheckboxGroup(choices=values, value=values)
    return update

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

    def __init__(self, actionEngine: ActionEngine, get_driver: callable):
        self.actionEngine = actionEngine
        self.get_driver = get_driver
        self.driver = None
        self.base_url = ""
        self.success = False
        self.error = ""

    def init_driver(self):
        def init_driver_impl(url):
            driver = self.get_driver()
            driver.goTo(url)
            driver.getScreenshot("screenshot.png")
            # This function is supposed to fetch and return the image from the URL.
            # Placeholder function: replace with actual image fetching logic.
            driver.destroy()
            return "screenshot.png"

        return init_driver_impl

    def process_instructions(self):
        def process_instructions_impl(query, url_input):
            driver = self.get_driver()
            driver.goTo(url_input)
            state = driver.getHtml()
            response = ""
            for text in self.actionEngine.get_action_streaming(query, state, url_input):
                # do something with text as they arrive.
                response += text
                yield response
            driver.destroy()

        return process_instructions_impl

    def __telemetry(self):
        def telemetry(query, code, html, url_input):
            screenshot = b""
            try:
                scr = open("screenshot.png", "rb")
                screenshot = base64.b64encode(scr.read())
            except:
                pass
            source_nodes = self.actionEngine.get_nodes(query, html)
            retrieved_context = "\n".join(source_nodes)
            send_telemetry(
                self.actionEngine.llm.metadata.model_name,
                code,
                screenshot,
                html,
                query,
                url_input,
                "Lavague-Launch",
                self.success,
                False,
                self.error,
                retrieved_context
            )

        return telemetry

    def __exec_code(self):
        def exec_code(url_input, code, full_code):
            driver_o = self.get_driver()
            self.error = ""
            code = self.actionEngine.cleaning_function(code)
            driver_o.goTo(url_input)
            html = driver_o.getHtml()
            driver_name, driver = driver_o.getDriver()  # define driver for exec
            
            from .format_utils import extract_code_from_funct, extract_imports_from_lines
            source_code_lines = extract_code_from_funct(self.get_driver)
            import_lines = extract_imports_from_lines(source_code_lines)
            try:
                code_to_exec = f"""
{import_lines}
{code}"""
                exec(code_to_exec)
                output = "Successful code execution"
                status = """<p style="color: green; font-size: 20px; font-weight: bold;">Success!</p>"""
                self.success = True
                full_code += code
                url_input = driver_o.getUrl()
                driver_o.getScreenshot("screenshot.png")
            except Exception as e:
                output = f"Error in code execution: {str(e)}"
                status = """<p style="color: red; font-size: 20px; font-weight: bold;">Failure! Open the Debug tab for more information</p>"""
                self.success = False
                self.error = repr(e)
            driver_o.destroy()
            return output, code, html, status, full_code, "screenshot.png", url_input

        return exec_code

    def __show_processing_message(self):
        return lambda: "Processing..."

    def run(self, base_url: str, instructions: List[str], server_port: int = 7860):
        """
        Launch the gradio demo

        Args:
            base_url (`str`): the url placeholder
            instructions (List[`str`]): List of default instructions
            max_tokens
        """
        
        
        with gr.Blocks(css=css) as demo:
            current_instruction = gr.State()
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
                        with gr.Accordion(label="Full code", open=False):
                            full_code = gr.Code(
                                value="", language="python", interactive=False
                            )
                        with gr.Row():
                            previous = gr.Button(value="Previous")
                            next = gr.Button(value="Next")
                        instructions_history = gr.HTML(html)

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
                        
            from bs4 import BeautifulSoup

            def append_item(new_item_text, soup):
                new_item = soup.new_tag("li")
                new_item.string = new_item_text
                soup.find('ul').append(new_item)

            def remove_item(item_index, soup):
                items = soup.find_all('li')
                if 0 <= item_index < len(items):
                    items[item_index].decompose()
                    
            def go_back(instructions_history, current_instruction):
                soup = BeautifulSoup(instructions_history, 'html.parser')

                current_instruction -= 1
                if current_instruction < 0:
                    current_instruction = 0
                items = soup.find_all('li')
                for item in items:
                    item.attrs.pop('style', None)
                items[current_instruction]['style'] = "background-color: #555;"
                output = soup.prettify()
                return output, current_instruction
            
            def go_forward(instructions_history, current_instruction):
                soup = BeautifulSoup(instructions_history, 'html.parser')

                current_instruction += 1
                items = soup.find_all('li')
                if current_instruction >= len(items):
                    current_instruction = len(items) - 1
                for item in items:
                    item.attrs.pop('style', None)
                items[current_instruction]['style'] = "background-color: #555;"
                output = soup.prettify()
                return output, current_instruction
                    
            def add_instruction(instruction, instructions_history, current_instruction):
                soup = BeautifulSoup(instructions_history, 'html.parser')
                new_item = soup.new_tag("li")
                new_item.string = instruction
                soup.find('ul').append(new_item)
                
                items = soup.find_all('li')
                for item in items:
                    item.attrs.pop('style', None)
                    
                current_instruction = len(items) - 1

                items[-1]['style'] = "background-color: #555;"

                output = soup.prettify()
                return output, current_instruction

            # Linking components
            url_input.submit(
                self.init_driver(),
                inputs=[url_input],
                outputs=[image_display],
                queue=True,
            )
            previous.click(go_back, 
                           inputs=[instructions_history, current_instruction], 
                           outputs=[instructions_history, current_instruction])
            
            next.click(go_forward, 
                       inputs=[instructions_history, current_instruction], 
                       outputs=[instructions_history, current_instruction])
            
            text_area.submit(
                self.__show_processing_message(), outputs=[status_html], queue=True, concurrency_limit=1
            ).then(
                self.process_instructions(),
                inputs=[text_area, url_input],
                outputs=[code_display],
                queue=True,
            ).then(
                self.__exec_code(),
                inputs=[url_input, code_display, full_code],
                outputs=[log_display, code_display, full_html, status_html, full_code, image_display, url_input],
                queue=True,
            ).then(
                self.__telemetry(),
                inputs=[text_area, code_display, full_html, url_input],
            ).then(add_instruction, 
                             inputs=[text_area, instructions_history, current_instruction], 
                             outputs=[instructions_history, current_instruction])
        demo.launch(server_port=server_port, share=True, debug=True)

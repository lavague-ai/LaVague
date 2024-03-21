
from .utils import load_action_engine

import os
import argparse
import importlib.util
from pathlib import Path
from tqdm import tqdm
import inspect

def import_from_path(path):
    # Convert the path to a Python module path
    module_name = Path(path).stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def build():
    parser = argparse.ArgumentParser(description='Process a file.')

    # Add the arguments
    parser.add_argument('--file_path',
                    type=str,
                    required=True,
                    help='the path to the file')

    parser.add_argument('--config_path',
                    type=str,
                    required=True,
                    help='the path to the Python config file')
    # Execute the parse_args() method
    args = parser.parse_args()
    
    file_path = args.file_path
    config_path = args.config_path
    
    # Load the action engine and driver from config file
    action_engine, get_driver = load_action_engine(config_path, streaming=False)
    
    driver = get_driver()
    
    # Gets the original source code of the get_driver method
    source_code = inspect.getsource(get_driver)

    # Split the source code into lines and remove the first line (method definition)
    source_code_lines = source_code.splitlines()[1:]
    source_code_lines = [line.strip() for line in source_code_lines[:-1]]
    
    # Execute the import lines
    import_lines = [line for line in source_code_lines if line.startswith("from") or line.startswith("import")] 
    exec("\n".join(import_lines))

    output = "\n".join(source_code_lines)

    with open(file_path, "r") as file:
        instructions = file.readlines()
        
        base_url = instructions[0].strip()
        instructions = [instruction.strip() for instruction in instructions[1:]]

        driver.get(base_url)
        output += f"\ndriver.get('{base_url.strip()}')\n"

        template_code = """\n########################################\n# Query: {instruction}\n# Code:\n{code}"""

        file_path = os.path.basename(file_path)
        file_path, _ = os.path.splitext(file_path)
        
        config_path = os.path.basename(config_path)
        config_path, _ = os.path.splitext(config_path)
        
        output_fn = file_path + "_" + config_path + ".py"
        
        for instruction in tqdm(instructions):
            print(f"Processing instruction: {instruction}")
            html = driver.page_source
            code, source_nodes = action_engine.get_action(instruction, html)
            try:
                exec(code)
            except Exception as e:
                print(f"Error in code execution: {code}")
                print("Error:", e)
                print(f"Saving output to {output_fn}")
                with open(output_fn, "w") as file:
                    file.write(output)
                    break
            output += "\n" + template_code.format(instruction=instruction, code=code).strip()
            
        
        print(f"Saving output to {output_fn}")
        with open(output_fn, "w") as file:
            file.write(output)
            
from typing import Optional, List
import gradio as gr
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By  # import used by generated selenium code
from selenium.webdriver.common.keys import (
    Keys,
)  # import used by generated selenium code
from .action_engine import ActionEngine


class CommandCenter:
    """
    CommandCenter allows you to launch a gradio demo powered by selenium and the ActionEngine

    Args:
        chromedriverPath(`str`):
            The path of the chromedriver executable
        chromePath (`Optional[str]`):
            The path of the chrome executable, if not specified, PATH will be used
        action_engine (`ActionEngine`):
            The action engine, with streaming enabled
    """

    title = """
    <div align="center">
    <h1>🌊 Welcome to LaVague</h1>
    <p>Redefining internet surfing by transforming natural language instructions into seamless browser interactions.</p>
    </div>
    """

    def __init__(
        self,
        action_engine: ActionEngine,
        driver
    ):
        self.action_engine = action_engine
        self.driver = driver

    def __process_url(self):
        def process_url(url):
            self.driver.get(url)
            self.driver.save_screenshot("screenshot.png")
            # This function is supposed to fetch and return the image from the URL.
            # Placeholder function: replace with actual image fetching logic.
            return "screenshot.png"

        return process_url

    def __process_instruction(self):
        def process_instructions(query, url_input):
            if url_input != self.driver.current_url:
                self.driver.get(url_input)
            state = self.driver.page_source
            query_engine = self.action_engine.get_query_engine(state)
            streaming_response = query_engine.query(query)

            source_nodes = streaming_response.get_formatted_sources(
                self.action_engine.max_chars_pc
            )

            response = ""

            for text in streaming_response.response_gen:
                # do something with text as they arrive.
                response += text
                yield response, source_nodes

        return process_instructions

    def __exec_code(self):
        def exec_code(code, full_code):
            code = self.action_engine.cleaning_function(code)
            html = self.driver.page_source
            driver = self.driver  # define driver for exec
            try:
                exec(code)
                output = "Successful code execution"
                status = """<p style="color: green; font-size: 20px; font-weight: bold;">Success!</p>"""
                full_code += code
            except Exception as e:
                output = f"Error in code execution: {str(e)}"
                status = """<p style="color: red; font-size: 20px; font-weight: bold;">Failure! Open the Debug tab for more information</p>"""
            return output, code, html, status, full_code

        return exec_code

    def __update_image_display(self):
        def update_image_display():
            self.driver.save_screenshot("screenshot.png")
            url = self.driver.current_url
            return "screenshot.png", url

        return update_image_display

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
                    with gr.Column():
                        source_display = gr.Code(
                            language="html",
                            label="Retrieved nodes",
                            interactive=False,
                            lines=20,
                        )
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
                self.__process_url(),
                inputs=[url_input],
                outputs=[image_display],
            )
            text_area.submit(
                self.__show_processing_message(), outputs=[status_html]
            ).then(
                self.__process_instruction(),
                inputs=[text_area, url_input],
                outputs=[code_display, source_display],
            ).then(
                self.__exec_code(),
                inputs=[code_display, full_code],
                outputs=[log_display, code_display, full_html, status_html, full_code],
            ).then(
                self.__update_image_display(),
                inputs=[],
                outputs=[image_display, url_input],
            )
        demo.launch(server_port=server_port, share=True, debug=True)

def launch():
    parser = argparse.ArgumentParser(description='Process a file.')

    # Add the arguments
    parser.add_argument('--file_path',
                    type=str,
                    required=True,
                    help='the path to the file')

    parser.add_argument('--config_path',
                    type=str,
                    required=True,
                    help='the path to the Python config file')
    # Execute the parse_args() method
    args = parser.parse_args()
    
    file_path = args.file_path
    config_path = args.config_path
    
    # Load the action engine and driver from config file
    action_engine, get_driver = load_action_engine(config_path, streaming=True)
    
    driver = get_driver()
    
    commandCenter = CommandCenter(action_engine, driver)

    with open(file_path, "r") as file:
        instructions = file.readlines()
        
        base_url = instructions[0].strip()
        instructions = [instruction.strip() for instruction in instructions[1:]]
        
    commandCenter.run(base_url, instructions)
import os
import re
import gradio as gr
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from lavague.ActionEngine import ActionEngine
from lavague.defaults import DefaultLocalLLM, DefaultLLM
from llama_index.llms.huggingface import HuggingFaceInferenceAPI
import re
from lavague.ActionEngine import ActionEngine

# Function to ensure Hugging Face API Token is available
HF_TOKEN = ""
WEBDRIVE_PATH = ""
MAX_CHARS = 1500

# Initialize WebDriver for Selenium
def init_webdriver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1600,900')
    chrome_options.binary_location = WEBDRIVE_PATH + "chrome-linux64/chrome"
    webdriver_service = Service(WEBDRIVE_PATH + "chromedriver-linux64/chromedriver")
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    return driver

def setup_gradio_demo(driver, base_url, instructions):
    action_engine = ActionEngine()  # Or use a specific configuration

    def extract_first_python_code(markdown_text):
        # Pattern to match the first ```python ``` code block
        pattern = r"```python(.*?)```"
        
        # Using re.DOTALL to make '.' match also newlines
        match = re.search(pattern, markdown_text, re.DOTALL)
        if match:
            # Return the first matched group, which is the code inside the ```python ```
            return match.group(1).strip()
        else:
            # Return None if no match is found
            return None
        
    def process_instruction(instructions, url_input):
        if url_input != driver.current_url:
            driver.get(url_input)
        source_code = driver.page_source
        query_engine = action_engine.get_query_engine(source_code)
        response = query_engine.query(instructions)
        source_nodes = response.get_formatted_sources(MAX_CHARS)
        return response.response, source_nodes

    def exec_code(code, source_nodes, full_code):
        code = extract_first_python_code(code)
        html = driver.page_source
        try:
            exec(code)
            output = "Successful code execution"
            status = """<p style="color: green; font-size: 20px; font-weight: bold;">Success!</p>"""
            full_code += code
        except Exception as e:
            output = f"Error in code execution: {str(e)}"
            status = """<p style="color: red; font-size: 20px; font-weight: bold;">Failure! Open the Debug tab for more information</p>"""
        return output, code, html, status, full_code

    def process_url(url):
        driver.get(url)
        driver.save_screenshot("screenshot.png")
        return "screenshot.png"

    def update_image_display(img):
        driver.save_screenshot("screenshot.png")
        url = driver.current_url
        return "screenshot.png", url

    def update_image_display(img):
        driver.save_screenshot("screenshot.png")
        url = driver.current_url
        return "screenshot.png", url

    title = """
    <div align="center">
    <h1>🌊 Welcome to LaVague</h1>
    <p>Redefining internet surfing by transforming natural language instructions into seamless browser interactions.</p>
    </div>
    """

    def show_processing_message():
        return "Processing..."

    with gr.Blocks() as demo:
        with gr.Tab("LaVague"):
            with gr.Row():
                gr.HTML(title)
            with gr.Row():
                url_input = gr.Textbox(value=base_url, label="Enter URL and press 'Enter' to load the page.")
            
            with gr.Row():
                with gr.Column(scale=7):
                    image_display = gr.Image(label="Browser", interactive=False)
                
                with gr.Column(scale=3):
                    with gr.Accordion(label="Full code", open=False):
                        full_code = gr.Code(value="", language="python", interactive=False)
                    code_display = gr.Code(label="Generated code", language="python",
                                            lines=5, interactive=True)
                    
                    status_html = gr.HTML()
            with gr.Row():
                with gr.Column(scale=8):
                    text_area = gr.Textbox(label="Enter instructions and press 'Enter' to generate code.")
                    gr.Examples(examples=instructions, inputs=text_area)
        with gr.Tab("Debug"):
            with gr.Row():
                with gr.Column():
                    log_display = gr.Textbox(interactive=False, lines=20)
                with gr.Column():
                    source_display = gr.Code(language="html", label="Retrieved nodes", interactive=False, lines=20)
            with gr.Row():
                with gr.Accordion(label="Full HTML", open=False):
                    full_html = gr.Code(language="html", label="Full HTML", interactive=False, lines=20)
    
        # Linking components
        url_input.submit(process_url, inputs=url_input, outputs=image_display)
        text_area.submit(show_processing_message, outputs=[status_html]).then(
            process_instruction, inputs=[text_area, url_input], outputs=[code_display, source_display]
            ).then(
            exec_code, inputs=[code_display, source_display, full_code], 
            outputs=[log_display, code_display, full_html, status_html, full_code]
        ).then(
            update_image_display, inputs=image_display, outputs=[image_display, url_input]
        )
    demo.launch(share=True, debug=True)

# Main function
def main():
    driver = init_webdriver()
    base_url = "https://huggingface.co/"
    instructions = ["Click on the Datasets item on the menu, between Models and Spaces",
                "Click on the search bar 'Filter by name', type 'The Stack', and press 'Enter'",
                "Scroll by 500 pixels",]
    setup_gradio_demo(driver, base_url, instructions)

if __name__ == '__main__':
    main()
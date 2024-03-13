import gradio as gr
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from lavague.ActionEngine import ActionEngine
from lavague.defaults import DefaultLocalLLM, DefaultLLM
from llama_index.llms.huggingface import HuggingFaceInferenceAPI

MAX_CHARS = 1500

action_engine = ActionEngine()

## Setup chrome options
chrome_options = Options()
chrome_options.add_argument("--headless") # Ensure GUI is off
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1600,900")

# Set path to chrome/chromedriver as per your configuration

chrome_options.binary_location = f"chrome-linux64/chrome"
webdriver_service = Service(f"chromedriver-linux64/chromedriver")


title = """
<div align="center">
  <h1>🌊 Welcome to LaVague</h1>
  <p>Redefining internet surfing by transforming natural language instructions into seamless browser interactions.</p>
</div>
"""

# Choose Chrome Browser
driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

# action_engine = ActionEngine(llm, embedder)

def process_url(url):
    driver.get(url)
    driver.save_screenshot("screenshot.png")
    # This function is supposed to fetch and return the image from the URL.
    # Placeholder function: replace with actual image fetching logic.
    return "screenshot.png"

def process_instruction(query):
    state = driver.page_source
    query_engine = action_engine.get_query_engine(state)
    streaming_response = query_engine.query(query)

    source_nodes = streaming_response.get_formatted_sources(MAX_CHARS)

    response = ""

    for text in streaming_response.response_gen:
    # do something with text as they arrive.
        response += text
        yield response, source_nodes

def exec_code(code):
    code = code.split("```")[0]
    try:
        exec(code)
        return "Successful code execution", code
    except Exception as e:
        output = f"Error in code execution: {str(e)}"
        return output, code

def update_image_display(img):
    driver.save_screenshot("screenshot.png")
    url = driver.current_url
    return "screenshot.png", url

def create_demo(base_url, instructions):
  with gr.Blocks() as demo:
      with gr.Row():
          gr.HTML(title)
      with gr.Row():
          url_input = gr.Textbox(value=base_url, label="Enter URL and press 'Enter' to load the page.")

      with gr.Row():
          with gr.Column(scale=8):
              image_display = gr.Image(label="Browser", interactive=False)

          with gr.Column(scale=2):
              text_area = gr.Textbox(label="Instructions")
              gr.Examples(examples=instructions, inputs=text_area,

              )
              generate_btn = gr.Button(value="Execute")
              code_display = gr.Code(label="Generated code", language="python",
                                    lines=5, interactive=False)
              with gr.Accordion(label="Logs", open=False) as log_accordion:
                  log_display = gr.Textbox(interactive=False)
                  source_display = gr.Textbox(label="Retrieved nodes", interactive=False)
      # Linking components
      url_input.submit(process_url, inputs=url_input, outputs=image_display)
      generate_btn.click(process_instruction, inputs=texst_area, outputs=[code_display, source_display]).then(
          exec_code, inputs=code_display, outputs=[log_display, code_display]
      ).then(
          update_image_display, inputs=image_display, outputs=[image_display, url_input]
      )
  demo.launch(share=True)

base_url = "https://huggingface.co/"

instructions = ["Click on the Datasets item on the menu, between Models and Spaces",
                "Click on the search bar 'Filter by name', type 'The Stack', and press 'Enter'",
                "Scroll by 500 pixels",]

create_demo(base_url, instructions)

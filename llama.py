from llama_index.core import Document
from llama_index.core.node_parser import CodeSplitter
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer
from llama_index.core import PromptTemplate
import time
from llama_index.llms.huggingface import HuggingFaceLLM
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import locale
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

from IPython.display import Image, display, clear_output
import requests
locale.getpreferredencoding = lambda: "UTF-8"

model_id = "HuggingFaceH4/zephyr-7b-gemma-v0.1"

quantization_config = BitsAndBytesConfig(
load_in_4bit=True,
bnb_4bit_use_double_quant=True,
bnb_4bit_quant_type="nf4",
bnb_4bit_compute_dtype=torch.bfloat16
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", quantization_config=quantization_config)

# We will stop generation as soon as the model outputs the end of Markdown to make inference faster
stop_token_id = [tokenizer.convert_tokens_to_ids("```"), tokenizer.convert_tokens_to_ids("``")]
llm = HuggingFaceLLM(model=model, tokenizer=tokenizer, max_new_tokens=1024, stopping_ids=stop_token_id)


embed_model = "BAAI/bge-small-en-v1.5"
embedder = HuggingFaceEmbedding(model_name=embed_model, device="cuda")

url = 'https://raw.githubusercontent.com/dhuynh95/LaVague/main/prompt_template.txt'
r = requests.get(url, allow_redirects=True)

if r.status_code == 200:
    with open('prompt_template.txt', 'wb') as file:
        file.write(r.content)
else:
    print("Failed to retrieve the file")

with open("prompt_template.txt", "r") as file:
  PROMPT_TEMPLATE_STR = file.read()
MAX_CHARS = 1500
K = 3

class ActionEngine:
    def __init__(self, llm, embedding):
        self.llm = llm
        self.embedding = embedding

    def _get_index(self, html):
        text_list = [html]
        documents = [Document(text=t) for t in text_list]

        splitter = CodeSplitter(
            language="html",
            chunk_lines=40,  # lines per chunk
            chunk_lines_overlap=200,  # lines overlap between chunks
            max_chars=MAX_CHARS,  # max chars per chunk
        )
        nodes = splitter.get_nodes_from_documents(documents)
        nodes = [node for node in nodes if node.text]

        index = VectorStoreIndex(nodes, embed_model=self.embedding)

        return index

    def get_action(self, query, state):
        html = state
        index = self._get_index(html)

        retriever = BM25Retriever.from_defaults(
            index=index,
            similarity_top_k=K,
        )

        response_synthesizer = get_response_synthesizer(llm=self.llm)

        # assemble query engine
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
        )

        prompt_template = PromptTemplate(PROMPT_TEMPLATE_STR)

        query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": prompt_template}
        )

        print("Querying LLM...")

        start_time = time.time()

        output = query_engine.query(query)

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Code generation time: {execution_time} seconds")

        print(f"Source nodes : {output.get_formatted_sources(MAX_CHARS)}")
        code = output.response.split("```")[0]

        return code
    
def execute_instructions(instructions, action_engine, driver, clear_display=True):
    for instruction in instructions:
        driver.save_screenshot('screenshot.png')
        if clear_display:
            clear_output(wait=True)
        display(Image(filename="screenshot.png"))
        print(f"Processing instruction: {instruction}")
        code = action_engine.get_action(instruction, driver.page_source)
        print(f"Code received: {code}")
        try:
            start_time = time.time()

            exec(code)

            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Code execution time: {execution_time} seconds")

            print("Code execution successful")

        except Exception as e:
            print(f"Error executing code: {e}")
        driver.save_screenshot('screenshot.png')
        if clear_display:
            clear_output(wait=True)
        display(Image(filename="screenshot.png"))  


## Setup chrome options
chrome_options = Options()
chrome_options.add_argument("--headless") # Ensure GUI is off
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1600,900")

# Set path to chrome/chromedriver as per your configuration
chrome_options.binary_location = "/home/namastex/dev/chrome-linux64/chrome"  # Adjust the path as needed
webdriver_service = Service("/home/namastex/dev/chromedriver-linux64/chromedriver")  # Adjust the path as needed

# Choose Chrome Browser
driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

action_engine = ActionEngine(llm, embedder)

driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
driver.get("https://huggingface.co/")

instructions = ["Click on the Datasets item on the menu, between Models and Spaces",
                "Click on the search bar 'Filter by name', type 'The Stack', and press 'Enter'",
                "Scroll by 500 pixels",]

execute_instructions(instructions, action_engine, driver)

driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
driver.get("https://www.irs.gov/")

instructions = ["Click on the 'Pay' item on the menu, between 'File' and 'Refunds'",
                "Click on 'Pay Now with Direct Pay' just below 'Pay from your Bank Account'",
                "Click on 'Make a Payment', just above 'Answers to common questions'",]

execute_instructions(instructions, action_engine, driver)

import dspy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
from getpass import getpass
import time
from pydantic import BaseModel
# Example HuggingFaceEmbedding class (assuming it's similar to HuggingFaceCodeGenerator)
from transformers import AutoModel, AutoTokenizer
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

import sys
import requests

# Load prompt template from URL
url = 'https://raw.githubusercontent.com/dhuynh95/LaVague/main/prompt_template.txt'
r = requests.get(url, allow_redirects=True)

PROMPT_TEMPLATE_STR = ''
if r.status_code == 200:
    PROMPT_TEMPLATE_STR = r.text
else:
    print("Failed to retrieve the file")

class ActionOutput(BaseModel):
    instruction: str
    selenium_code: str

class InferenceInput(BaseModel):
    instruction: str
    current_page_html: str

# Define necessary DSPy signatures
class ActionRequest(dspy.Signature):
    instruction = dspy.InputField(desc="Natural language instruction for a web action")
    current_page_html = dspy.InputField(desc="HTML content of the current page for context")
    selenium_code = dspy.OutputField(desc="Generated Selenium code to execute the action")

class SeleniumExecution(dspy.Signature):
    selenium_code = dspy.InputField(desc="Selenium code to be executed")
    execution_result = dspy.OutputField(desc="Result of the Selenium code execution, e.g., success or failure")


# Initialization part
model_id = "BAAI/bge-small-en-v1.5"  # Specify your model ID here
embedder = HuggingFaceEmbedding(model_id)

class HuggingFaceEmbedding:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def get_embeddings(self, text):
        inputs = self.tokenizer(text, return_tensors="pt")
        outputs = self.model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings

    def get_text_embedding_batch(self, texts, batch_size=32, **kwargs):
        # Initialize a placeholder for batch embeddings
        batch_embeddings = []

        # Process texts in batches to generate embeddings
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_inputs = self.tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True)
            with torch.no_grad():
                batch_outputs = self.model(**batch_inputs)
            batch_embeddings.extend(batch_outputs.last_hidden_state.mean(dim=1).cpu().numpy())

        return batch_embeddings



class HuggingFaceCodeGenerator(dspy.Module):
    def __init__(self, model_name, tokenizer_name):
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
    
    def forward(self, instruction, context):
        prompt = self._create_prompt(instruction, context)
        inputs = self.tokenizer.encode(prompt, return_tensors='pt')
        outputs = self.model.generate(inputs, max_length=512)[0]
        code = self.tokenizer.decode(outputs, skip_special_tokens=True)
        return code

    def _create_prompt(self, instruction, context):
        return f"Instruction: {instruction}\nContext: {context}\n\nSelenium Code:"


class DocumentProcessor(dspy.Module):
    def __init__(self, embedder_model_name):
        super().__init__()
        self.embedder = SentenceTransformer(embedder_model_name)

    def forward(self, html_content):
        text = self.process_html(html_content)
        embeddings = self.embed_text(text)
        return embeddings

    def process_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return text

    def embed_text(self, text):
        embeddings = self.embedder.encode([text], convert_to_tensor=True)
        return embeddings

# Inference Engine Module for generating Selenium code
class InferenceEngineModule(dspy.Module):
    def __init__(self):
        super().__init__()  # Initialize the module without setting a signature here.

    def forward(self, instruction, current_page_html):
        # Here, instead of validating data against the signature (as it seemed to be intended),
        # directly use the provided 'instruction' and 'current_page_html' to perform your task.
        
        # Generate Selenium code based on the instruction and HTML content.
        # Replace the following line with your actual code generation logic.
        # For demonstration, let's say dspy.predict does the job.
        response = dspy.predict(instruction=instruction, current_page_html=current_page_html, max_tokens=200)
        selenium_code = response['choices'][0]['text'].strip()
        
        return selenium_code



# Executor for running Selenium code
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class SeleniumExecutor:
    def __init__(self, driver_config):
        # Setup chrome options based on driver_config
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Ensure GUI is off
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1600,900")

        if "binary_location" in driver_config:
            chrome_options.binary_location = driver_config["binary_location"]

        # Initialize WebDriver Service with the executable_path
        chrome_service = Service(executable_path=driver_config["executable_path"])

        # Initialize WebDriver with provided Service and Chrome options
        self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    def execute(self, selenium_code):
        # Define 'driver' as a local variable that references 'self.driver'
        driver = self.driver
        # Execute the selenium code here, with 'driver' now defined in this scope
        try:
            exec(selenium_code)
        except Exception as e:
            print(f"Error executing Selenium code: {e}")




import hashlib
from typing import List, Dict

class ActionEngine:
    MAX_CHARS = 1500
    K = 3

    def __init__(self, llm, embedding):
        self.llm = llm
        self.embedding = embedding
        self.embeddings_cache = {}
        self.query_results_cache = {}

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _get_index(self, html: str):
        text_list = [html]
        documents = [Document(text=t) for t in text_list]

        splitter = CodeSplitter(
            language="html",
            chunk_lines=40,
            chunk_lines_overlap=200,
            max_chars=self.MAX_CHARS,
        )
        nodes = splitter.get_nodes_from_documents(documents)
        nodes = [node for node in nodes if node.text]

        # Retrieve or use cached embeddings for all node texts
        for node in nodes:
            node_text_hash = self._hash_text(node.text)
            if node_text_hash in self.embeddings_cache:
                embedding = self.embeddings_cache[node_text_hash]
            else:
                embedding = self.embedding.get_text_embedding_batch([node.text])[0].tolist()
                self.embeddings_cache[node_text_hash] = embedding
            node.embedding = embedding

        index = VectorStoreIndex(nodes, embed_model=self.embedding)
        return index

    def get_action(self, query: str, state: str):
        query_hash = self._hash_text(query)
        if query_hash in self.query_results_cache:
            return self.query_results_cache[query_hash]

        html = state
        index = self._get_index(html)
        
        # Logic to use the index for retrieving actions goes here...
        # For example, creating and using a RetrieverQueryEngine as before:
        retriever = BM25Retriever.from_defaults(index=index, similarity_top_k=self.K)
        response_synthesizer = get_response_synthesizer(llm=self.llm)
        query_engine = RetrieverQueryEngine(retriever=retriever, response_synthesizer=response_synthesizer)
        prompt_template = PromptTemplate(PROMPT_TEMPLATE_STR)
        query_engine.update_prompts({"response_synthesizer:text_qa_template": prompt_template})

        print("Querying LLM...")
        start_time = time.time()
        output = query_engine.query(query)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Code generation time: {execution_time} seconds")
        print(f"Source nodes: {output.get_formatted_sources(self.MAX_CHARS)}")
        code = output.response.split("```")[0]

        # Cache the query result for future use
        self.query_results_cache[query_hash] = code
        return code


# Assuming the rest of your setup remains the same as provided

# Enhanced LaVagueApp class
class LaVagueApp:
    def __init__(self, driver_config):
        self.driver_config = driver_config
        self.setup_models()
        self.setup_action_engine()
        self.selenium_executor = SeleniumExecutor(driver_config)

    def setup_models(self):
        model_id = "HuggingFaceH4/zephyr-7b-gemma-v0.1"
        quantization_config = BitsAndBytesConfig(load_in_4bit=True, 
                                                 bnb_4bit_use_double_quant=True, 
                                                 bnb_4bit_quant_type="nf4", 
                                                 bnb_4bit_compute_dtype=torch.bfloat16)
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", 
                                                     quantization_config=quantization_config)
        self.llm = HuggingFaceLLM(model=model, tokenizer=tokenizer, 
                                  max_new_tokens=1024, stopping_ids=[tokenizer.eos_token_id])

        embed_model = "BAAI/bge-small-en-v1.5"
        self.embedder = HuggingFaceEmbedding(embed_model)

        with open("prompt_template.txt", "r") as file:
            self.prompt_template = file.read()

    def setup_action_engine(self):
        self.action_engine = ActionEngine(self.llm, self.embedder)

    def execute_instructions(self, instructions, url, clear_display=True):
        # Navigate to the URL
        self.selenium_executor.driver.get(url)
        
        for instruction in instructions:
            print(f"Processing instruction: {instruction}")
            action_output = self.action_engine.get_action(instruction, self.selenium_executor.driver.page_source)
            if isinstance(action_output, dict):
                selenium_code = action_output['selenium_code']
            else:
                selenium_code = action_output  # Direct string output if not dict
            
            print(f"Generated Selenium code: \n{selenium_code}")
            try:
                start_time = time.time()
                
                # Execute the code within the SeleniumExecutor context
                self.selenium_executor.execute(selenium_code)
                
                end_time = time.time()
                execution_time = end_time - start_time
                print(f"Code execution time: {execution_time} seconds")
                print("Instruction executed successfully.")
            except Exception as e:
                print(f"Error during execution: {e}")
            
            if clear_display and 'ipykernel' in sys.modules:
                from IPython.display import clear_output, display, Image
                self.selenium_executor.driver.save_screenshot('screenshot.png')
                clear_output(wait=True)
                display(Image('screenshot.png'))






# Ensure all necessary classes like SeleniumExecutor, ActionEngine, and others are correctly defined.

# Remember to adjust paths, model IDs, and configurations according to your specific setup and requirements.


# Setup and initialization code here, similar to your provided structure

# Instantiate and use LaVagueApp as needed



# Setup for Hugging Face and LLM
try:
    HF_TOKEN = os.environ.get("HF_TOKEN") or getpass('Enter your HF Token: ')
except:
    HF_TOKEN = getpass('Enter your HF Token: ')

llm = dspy.OpenAI(model='gpt-3.5-turbo', api_key=HF_TOKEN)
dspy.settings.configure(lm=llm)

# Example driver configuration with specific paths
driver_config = {
    "executable_path": "/home/namastex/dev/chromedriver-linux64/chromedriver",
    "binary_location": "/home/namastex/dev/chrome-linux64/chrome",
    "options": Options().add_argument("--headless")  # Continue adding any other options as needed
}

# Include the logic for initializing your LLM, embedding models, and setting up the web driver here

# Initialize the ActionEngine with the LLM and embedding model
action_engine = ActionEngine(llm, embedder)

# Initialize your LaVagueApp with appropriate driver configuration
app = LaVagueApp(driver_config=driver_config)  # Ensure driver_config is defined properly

# Example usage with defined instructions for a specific URL
url = "https://huggingface.co/"
instructions = [
    "Click on the Datasets item on the menu, between Models and Spaces",
    "Click on the search bar 'Filter by name', type 'The Stack', and press 'Enter'",
    "Scroll by 500 pixels",
]
app.execute_instructions(instructions, url, clear_display=True)

# You can repeat the process for another URL and a new set of instructions

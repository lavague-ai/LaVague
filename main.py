from llama_index.core import Document
from llama_index.core.node_parser import CodeSplitter
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer
from llama_index.core import PromptTemplate

from selenium import webdriver

import logging

import time

MAX_CHARS = 1000
K = 5
  
with open("prompt_template.txt", "r") as f:
    PROMPT_TEMPLATE_STR = f.read()

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
        
        start_time = time.time()

        index = VectorStoreIndex(nodes, embed_model=self.embedding)

        end_time = time.time()
        execution_time = end_time - start_time
        logging.debug(f"Indexing time: {execution_time} seconds")
        
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
        
        start_time = time.time()

        output = query_engine.query(query)

        end_time = time.time()
        execution_time = end_time - start_time
        logging.debug(f"Querying time: {execution_time} seconds")
        
        code = output.response.split("```")[0]

        return code

import argparse
import time

from llama_index.llms.huggingface import HuggingFaceInferenceAPI, HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceInferenceAPIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

import nest_asyncio
nest_asyncio.apply()

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Process some instructions.")
    parser.add_argument('file_path', type=str, help='Path to the instructions file')
    parser.add_argument('--local', action='store_true', help='Flag indicating local execution')
    parser.add_argument('--llm_model', type=str, default="google/gemma-7b-it", help='LLM model name')
    parser.add_argument('--embed_model', type=str, default="BAAI/bge-small-en-v1.5", help='Embedding model name')
    parser.add_argument('--hf_token', type=str, help='Hugging Face API key')
    parser.add_argument('--driver', choices=['chrome', 'firefox'], default="firefox", help='Driver type (chrome or firefox)')
    parser.add_argument('--log_level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Logging level')

    args = parser.parse_args()
    
    # Set logging level
    logging.basicConfig(level=args.log_level)
    
    args = parser.parse_args()
    with open(args.file_path, 'r') as file:
        instructions = file.readlines()
        
    if args.driver == 'chrome':
        driver = webdriver.Chrome()
    else:
        driver = webdriver.Firefox()
        
    if args.local:
        llm = HuggingFaceLLM(model_name=args.llm_model, auth_token=args.hf_token)
        
        embedder = HuggingFaceEmbedding(model_name=args.embed_model, auth_token=args.hf_token)
    else:
        llm = HuggingFaceInferenceAPI(
            model_name=args.llm_model, token=args.hf_token
        )

        embedder = HuggingFaceInferenceAPIEmbedding(model_name=args.embed_model, token=args.hf_token)
        
    action_engine = ActionEngine(llm, embedder)
        
    for instruction in instructions:
        code = action_engine.get_action(instruction, driver.page_source)
        # Process each instruction here
        try:
            start_time = time.time()

            exec(code)

            end_time = time.time()
            execution_time = end_time - start_time
            logging.debug(f"Code execution time: {execution_time} seconds")
            
            logging.info("Code execution successful")
            
        except Exception as e:
            logging.error(f"Error executing code: {e}")
            
    time.sleep(10)
    driver.quit()
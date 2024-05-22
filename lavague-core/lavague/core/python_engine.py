from lavague.core.context import Context, get_default_context
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.agent import ReActAgent
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.tools import FunctionTool
import trafilatura
import os

def extract_text_content(instruction, html_file):
    """
    Extract the text content of the HTML page
    {
        "user": "Use the content of the HTML page to answer the question 'How was falcon-11B trained?'",
        "agent": "I need to use the 'extract_text_content' tool to get information about how Falcon-11B was trained.",
        "action": "extract_text_content",
        "action_input": {
            "instruction": "How was Falcon-11B trained?",
            "html_file": "example.html"
        },
    },
    {
        "user": "Use the content of the HTML page to answer the question 'What are the main types of renewable energy?'",
        "agent": "I need to use the 'extract_text_content' tool to get information about the main types of renewable energy.",
        "action": "extract_text_content",
        "action_input": {
            "instruction": "How was Falcon-11B trained?",
            "html_file": "example.html"
        },
    },
    {
        "user": "Use the content of Yann LeCun's Wikipedia page to make a summary of his life.",
        "agent": "I need to use the 'extract_text_content' tool to get information from Yann LeCun's Wikipedia page to make a summary of his life.",
        "action": "extract_text_content",
        "action_input": {
            "instruction": "How was Falcon-11B trained?",
            "html_file": "example.html"
        },
    }
    """
    with open(html_file, 'rb') as f:
        html = f.read()
        os.remove(html_file)
    page_content = trafilatura.extract(html)
    documents = [Document(text=page_content)]
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()
    output = query_engine.query(instruction).response
    return output

class PythonEngine:
    """
    This engine generates python code which doesn't interactor with a web driver, and doesn't require RAG over an html page
    """

    def __init__(
        self,
        llm: BaseLLM = get_default_context().llm,
    ):
        self.llm: BaseLLM = llm
        self.extract_tool = FunctionTool.from_defaults(fn=extract_text_content, return_direct=True)
        self.agent = ReActAgent.from_tools([self.extract_tool], llm=self.llm, verbose=True)

    @classmethod
    def from_context(
        cls,
        context: Context,
    ):
        return cls(context.llm)
    
    def run(self, instruction : str):
        return self.agent.chat(instruction)


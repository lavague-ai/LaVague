from typing import Callable, Optional
from llama_index.core import Document
from llama_index.core.node_parser import CodeSplitter
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer
from llama_index.core import PromptTemplate
from llama_index.core.service_context_elements.llm_predictor import LLMPredictorType
from llama_index.core.embeddings.utils import EmbedType
import re


def extract_first_python_code(markdown_text: str):
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


class ActionEngine:
    """
    ActionEngine levergaes the llm model and the embedding model to output code from the prompt and the html page.

    Args:
        llm (`LLMPredictorType`):
            The llm that will be used the generate the python code
        embedding (`EmbedType`):
            The embedding model to encode the html page and the prompt
        prompt (`str`):
            The initial prompt given to the llm, later completed by chunks of the html page and the query
        cleaning_function (`Callable[[str], Optional[str]]`):
            Function to extract the python code from the llm output
        top_k (`int`):
            The top K relevant chunks from the html page will be used in the final query
        max_chars_pc (`int`):
            A chunk can't be larger than max_chars_pc
        streaming (`bool`)
    """

    def __init__(
        self,
        llm: LLMPredictorType,
        embedding: EmbedType,
        prompt: str,
        cleaning_function: Callable[[str], Optional[str]] = extract_first_python_code,
        top_k: int = 3,
        max_chars_pc: int = 1500,
        streaming: bool = True,
    ):
        self.llm = llm
        self.embedding = embedding
        self.prompt = prompt
        self.cleaning_function = cleaning_function
        self.top_k = top_k
        self.max_chars_pc = max_chars_pc
        self.streaming = streaming

    def _get_index(self, html):
        text_list = [html]
        documents = [Document(text=t) for t in text_list]

        splitter = CodeSplitter(
            language="html",
            chunk_lines=40,  # lines per chunk
            chunk_lines_overlap=200,  # lines overlap between chunks
            max_chars=self.max_chars_pc,  # max chars per chunk
        )
        nodes = splitter.get_nodes_from_documents(documents)
        nodes = [node for node in nodes if node.text]

        index = VectorStoreIndex(nodes, embed_model=self.embedding)

        return index

    def get_query_engine(self, state):
        """
        Get the llama-index query engine

        Args:
            state (`str`): The initial html page

        Return:
            `RetrieverQueryEngine`
        """
        html = state
        index = self._get_index(html)

        retriever = BM25Retriever.from_defaults(
            index=index, similarity_top_k=self.top_k
        )

        response_synthesizer = get_response_synthesizer(
            streaming=self.streaming, llm=self.llm
        )

        # assemble query engine
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
        )

        prompt_template = PromptTemplate(self.prompt)

        query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": prompt_template}
        )

        return query_engine

    def get_action(self, query: str, html: str):
        """
        Generate the code from a query and an html page, only works if streaming=False

        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page
            html (`str`): The html page

        Return:
            (`str`, `str`): The generated code, and the sources which were used
        """
        query_engine = self.get_query_engine(html, streaming=False)
        response = query_engine.query(query)
        source_nodes = response.get_formatted_sources(
            self.max_chars_pc
        )  # HTML sources with which the code was generated
        code = response.response
        code = self.cleaning_function(code)
        return code, source_nodes

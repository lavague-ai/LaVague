from typing import Callable, Optional, Generator
from abc import ABC, abstractmethod
from llama_index.core import Document
from llama_index.core.node_parser import CodeSplitter
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer
from llama_index.core import PromptTemplate
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.embeddings.base import BaseEmbedding
from .prompts import SELENIUM_PROMPT
from .defaults import default_python_code_extractor


class BaseActionEngine(ABC):
    """
    Abstract class for ActionEngine
    """

    @abstractmethod
    def get_action(self, query: str, html: str) -> str:
        """
        Generate the code from a query and an html page, and clean it to extract the code

        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page
            html (`str`): The html page

        Return:
            `str`: The generated code
        """
        pass

    @abstractmethod
    def get_action_streaming(self, query: str, html: str) -> Generator[str, None, None]:
        """
        Generate the code with streaming from a query and an html page (without cleaning)

        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page
            html (`str`): The html page

        Return:
            `str`: The generated code
        """
        pass


class ActionEngine(BaseActionEngine):
    """
    ActionEngine leverages the llm model and the embedding model to output code from the prompt and the html page.

    Args:
        llm (`LLMPredictorType`):
            The llm that will be used the generate the python code
        embedding (`EmbedType`):
            The embedding model to encode the html page and the prompt
        prompt_template (`str`):
            The prompt_template given to the llm, later completed by chunks of the html page and the query
        cleaning_function (`Callable[[str], Optional[str]]`):
            Function to extract the python code from the llm output
        top_k (`int`):
            The top K relevant chunks from the html page will be used in the final query
        max_chars_pc (`int`):
            A chunk can't be larger than max_chars_pc
    """

    def __init__(
        self,
        llm: BaseLLM,
        embedder: BaseEmbedding,
        prompt_template: str = SELENIUM_PROMPT,
        cleaning_function: Callable[
            [str], Optional[str]
        ] = default_python_code_extractor,
        top_k: int = 3,
        max_chars_pc: int = 1500,
    ):
        self.llm = llm
        self.embedder = embedder
        self.prompt_template = prompt_template
        self.cleaning_function = cleaning_function
        self.top_k = top_k
        self.max_chars_pc = max_chars_pc

    def _get_index(self, html):
        text_list = [html]
        documents = [Document(text=t) for t in text_list]

        splitter = CodeSplitter(
            language="html",
            chunk_lines=50,  # lines per chunk
            chunk_lines_overlap=15,  # lines overlap between chunks
            max_chars=2000,  # max chars per chunk
        )
        nodes = splitter.get_nodes_from_documents(documents)
        nodes = [node for node in nodes if node.text]

        index = VectorStoreIndex(nodes, embed_model=self.embedder)

        return index

    def get_query_engine(
        self, state: str, streaming: bool = True
    ) -> RetrieverQueryEngine:
        """
        Get the llama-index query engine

        Args:
            state (`str`): The initial html page
            streaming (`bool`)

        Return:
            `RetrieverQueryEngine`
        """
        html = state
        index = self._get_index(html)

        retriever = BM25Retriever.from_defaults(
            index=index, similarity_top_k=self.top_k
        )

        response_synthesizer = get_response_synthesizer(
            streaming=streaming, llm=self.llm
        )

        # assemble query engine
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
        )

        prompt_template = PromptTemplate(self.prompt_template)

        query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": prompt_template}
        )

        return query_engine

    def get_action(self, query: str, html: str) -> str:
        query_engine = self.get_query_engine(html, streaming=False)
        response = query_engine.query(query)
        code = response.response
        code = self.cleaning_function(code)
        return code

    def get_action_streaming(self, query: str, html: str) -> Generator[str, None, None]:
        query_engine = self.get_query_engine(html, streaming=True)
        streaming_response = query_engine.query(query)
        for text in streaming_response.response_gen:
            yield text


class TestActionEngine(BaseActionEngine):
    """
    TestActionEngine removes any querying and returns a default code - is used to quickly test software

    Args:
        dummy_code: (`str`)
    """

    def __init__(self, dummy_code: str):
        self.dummy_code = dummy_code

    def get_action(self, query: str, html: str) -> str:
        return self.dummy_code

    def get_action_streaming(self, query: str, html: str) -> Generator[str, None, None]:
        return self.dummy_code

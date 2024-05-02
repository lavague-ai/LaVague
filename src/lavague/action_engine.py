from typing import Callable, Optional, Generator, List
from abc import ABC, abstractmethod
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer
from llama_index.core import PromptTemplate, QueryBundle
from llama_index.core.base.llms.base import BaseLLM

from .prompts import SELENIUM_PROMPT
from .defaults import default_python_code_extractor
from .retrievers import BaseHtmlRetriever


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
        retriever (`BaseHtmlRetriever`)
            The retriever used to extract context from the html page
        prompt_template (`str`):
            The prompt_template given to the llm, later completed by chunks of the html page and the query
        cleaning_function (`Callable[[str], Optional[str]]`):
            Function to extract the python code from the llm output
    """

    def __init__(
        self,
        llm: BaseLLM,
        retriever: BaseHtmlRetriever,
        prompt_template: str = SELENIUM_PROMPT,
        cleaning_function: Callable[
            [str], Optional[str]
        ] = default_python_code_extractor,
    ):
        self.llm = llm
        self.retriever = retriever
        self.prompt_template = prompt_template
        self.cleaning_function = cleaning_function

    def get_query_engine(
        self, html: str, streaming: bool = True
    ) -> RetrieverQueryEngine:
        """
        Get the llama-index query engine

        Args:
            html: (`str`)
            streaming (`bool`)

        Return:
            `RetrieverQueryEngine`
        """

        response_synthesizer = get_response_synthesizer(
            streaming=streaming, llm=self.llm
        )

        # assemble query engine
        query_engine = RetrieverQueryEngine(
            retriever=self.retriever.to_llama_index(html),
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
    
    def action_from_context(self, context: str, query: str) -> str: 
        prompt = self.prompt_template.format(context_str=context, query_str=query)

        response = self.llm.complete(prompt).text

        generated_code = self.cleaning_function(response)
        return generated_code
    
    def get_nodes(self, query: str, html: str) -> List[str]:
        """
        Get the nodes from the html page

        Args:
            html (`str`): The html page

        Return:
            `List[str]`: The nodes
        """
        source_nodes = self.retriever._retrieve_html(html, QueryBundle(query_str=query))
        source_nodes = [node.text for node in source_nodes]
        return source_nodes

    def get_action_streaming(self, query: str, html: str) -> Generator[str, None, None]:
        query_engine = self.get_query_engine(html, streaming=True)
        streaming_response = query_engine.query(query)
        for text in streaming_response.response_gen:
            yield text

    def get_action_streaming_vscode(self, query: str, html: str, url: str) -> Generator[str, None, None]:
        from .telemetry import send_telemetry

        success = True
        err = ""
        full_text = ""
        try:
            query_engine = self.get_query_engine(html, streaming=True)
            streaming_response = query_engine.query(query)
            for text in streaming_response.response_gen:
                full_text += text
                yield text
        except Exception as e:
            err = repr(e)
            success = False
        finally:
            source_nodes = self.get_nodes(query, html)
            retrieved_context = "\n".join(source_nodes)
            send_telemetry(self.llm.metadata.model_name, full_text, "", html, query, url, "lavague-vscode", success, False, err, retrieved_context)

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
    
    def get_nodes(self, query: str, html: str) -> List[str]:
        return ["test", "test"]

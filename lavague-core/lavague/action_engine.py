from __future__ import annotations
from typing import Optional, Generator
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer
from llama_index.core import PromptTemplate
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.embeddings.base import BaseEmbedding
from .extractors import BaseExtractor
from .retrievers import BaseHtmlRetriever
from .driver import BaseDriver
from .action_context import ActionContext

class ActionEngine:
    """
    ActionEngine leverages the llm model and the embedding model to output code from the prompt and the html page.

    Args:
        driver (`BaseDriver`):
            The Web driver used to interact with the headless browser
        llm (`BaseLLM`):
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
        driver: BaseDriver,
        llm: BaseLLM,
        embedding: BaseEmbedding,
        retriever: BaseHtmlRetriever,
        prompt_template: str,
        extractor: BaseExtractor,
    ):
        self.driver = driver
        self.llm = llm
        self.embedding = embedding
        self.retriever = retriever
        self.prompt_template = prompt_template
        self.extractor = extractor
    
    def from_context(context: ActionContext) -> ActionEngine:
        return ActionEngine(context.driver, context.llm, context.embedding, context.retriever, context.prompt_template, context.extractor)

    def _get_query_engine(
        self, streaming: bool = True
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
            retriever=self.retriever.to_llama_index(self.driver, self.embedding),
            response_synthesizer=response_synthesizer,
        )

        prompt_template = PromptTemplate(self.prompt_template)

        query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": prompt_template}
        )

        return query_engine

    def get_action(self, query: str, url: str = None) -> Optional[str]:
        """
        Generate the code from a query and an url, if the url is None, the driver's current url is used, extract the code, and execute it to be ready for the next instruction

        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page
            url (`str`): The url of the target html page

        Return:
            `str`: The generated code
        """
        if url is not None:
            self.driver.goto(url)
        query_engine = self._get_query_engine(streaming=False)
        response = query_engine.query(query)
        code = response.response
        code = self.extractor.extract(code)
        try:
            self.driver.exec_code(code)
            return code
        except Exception as e:
            print(f"Error in code execution:\n{code}")
            print("Error:", e)
            return None

    def get_action_streaming(self, query: str, url: str = None) -> Generator[str, None, None]:
        """
        Stream code from a query and an url, if the url is None, the driver's current url is used.

        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page
            url (`str`): The url of the target html page

        Return:
            `Generator[str, None, None]`: Generator for the generated code
        """
        if url is not None:
            self.driver.goto(url)
        query_engine = self._get_query_engine(streaming=True)
        streaming_response = query_engine.query(query)
        for text in streaming_response.response_gen:
            yield text

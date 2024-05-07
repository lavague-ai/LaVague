from __future__ import annotations
from typing import Optional, Generator
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer
from llama_index.core import PromptTemplate
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.embeddings.base import BaseEmbedding
from lavague.core.extractors import BaseExtractor
from lavague.core.retrievers import BaseHtmlRetriever
from lavague.core.base_driver import BaseDriver
from lavague.core.action_context import ActionContext

class ActionEngine:
    """
    ActionEngine leverages the llm model and the embedding model to output code from the prompt and the html page.

    Args:
        driver (`BaseDriver`):
            The Web driver used to interact with the headless browser
        llm (`BaseLLM`):
            The llm that will be used the generate the python code
        embedding: (`BaseEmbedding`)
            The embedder used by the retriever
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
        prompt_template: PromptTemplate,
        extractor: BaseExtractor,
    ):
        self.driver = driver
        self.llm = llm
        self.embedding = embedding
        self.retriever = retriever
        self.prompt_template = prompt_template.partial_format(driver_capability=driver.get_capability())
        self.extractor = extractor

    def from_context(driver: BaseDriver, context: ActionContext) -> ActionEngine:
        return ActionEngine(driver, context.llm, context.embedding, context.retriever, context.prompt_template, context.extractor)

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

        query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": self.prompt_template}
        )

        return query_engine

    def get_action(self, query: str) -> Optional[str]:
        """
        Generate the code from a query

        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page

        Return:
            `str`: The generated code
        """
        query_engine = self._get_query_engine(streaming=False)
        response = query_engine.query(query)
        code = response.response
        return self.extractor.extract(code)

    def get_action_streaming(self, query: str) -> Generator[str, None, None]:
        """
        Stream code from a query and an url

        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page
            url (`str`): The url of the target html page

        Return:
            `Generator[str, None, None]`: Generator for the generated code
        """
        query_engine = self._get_query_engine(streaming=True)
        streaming_response = query_engine.query(query)
        for text in streaming_response.response_gen:
            yield text

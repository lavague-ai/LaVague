from __future__ import annotations
from typing import Optional, Generator, List
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer, PromptTemplate, QueryBundle
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.embeddings.base import BaseEmbedding
from lavague.core.extractors import BaseExtractor
from lavague.core.retrievers import BaseHtmlRetriever
from lavague.core.base_driver import BaseDriver
from lavague.core.context import Context, get_default_context


class ActionEngine:
    """
    ActionEngine leverages the llm model and the embedding model to output code from the prompt and the html page.

    Args:
        driver (`BaseDriver`):
            The Web driver used to interact with the headless browser
    """

    def __init__(
        self,
        driver: BaseDriver,
        context: Optional[Context] = None,
    ):
        if context is None:
            context = get_default_context()
        self.driver: BaseDriver = driver
        self.llm: BaseLLM = context.llm
        self.embedding: BaseEmbedding = context.embedding
        self.retriever: BaseHtmlRetriever = context.retriever
        self.prompt_template: PromptTemplate = context.prompt_template.partial_format(
            driver_capability=driver.get_capability()
        )
        self.extractor: BaseExtractor = context.extractor

    def _get_query_engine(self, streaming: bool = True) -> RetrieverQueryEngine:
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

    def get_nodes(self, query: str) -> List[str]:
        """
        Get the nodes from the html page

        Args:
            html (`str`): The html page

        Return:
            `List[str]`: The nodes
        """
        source_nodes = self.retriever.retrieve_html(
            self.driver, self.embedding, QueryBundle(query_str=query)
        )
        source_nodes = [node.text for node in source_nodes]
        return source_nodes

    def get_action_from_context(self, context: str, query: str) -> str:
        """
        Generate the code from a query and a context
        """
        prompt = self.prompt_template.format(context_str=context, query_str=query)
        response = self.llm.complete(prompt).text
        code = self.extractor.extract(response)
        return code

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

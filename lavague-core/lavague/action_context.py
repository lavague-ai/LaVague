from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.embeddings.base import BaseEmbedding
from .extractors import BaseExtractor
from .retrievers import BaseHtmlRetriever
from .driver import BaseDriver

class ActionContext:
    """Set the context which will be used thourough the action generation pipeline."""

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

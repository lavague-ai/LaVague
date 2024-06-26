from lavague.core.base_driver import BaseDriver
from lavague.core.retrievers import BaseHtmlRetriever
from llama_index.core.llms import LLM
from llama_index.core.multi_modal_llms import MultiModalLLM
from llama_index.core.embeddings import BaseEmbedding

DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.0
DEFAULT_CONTEXT = None


class Context:
    """Set the context which will be used thourough the action generation pipeline."""

    def __init__(
        self,
        llm: LLM,
        mm_llm: MultiModalLLM,
        retriever: BaseHtmlRetriever,
        driver: BaseDriver,
    ):
        """
        llm (`LLM`):
            The llm that will be used the generate the python code
        mm_llm (`MultiModalLLM`):
            The multimodal llm that will be used by the world model
        retriever: (`BaseHtmlRetriever`)
            The html retriever to use
        driver: (`BaseDriver`)
            The driver to use
        """
        self.llm = llm
        self.mm_llm = mm_llm
        self.retriever = retriever
        self.driver = driver


def get_default_context() -> Context:
    try:
        global DEFAULT_CONTEXT
        from lavague.contexts.openai import OpenaiContext

        if DEFAULT_CONTEXT is None:
            DEFAULT_CONTEXT = OpenaiContext()

        return DEFAULT_CONTEXT

    except ImportError:
        raise ImportError(
            "`lavague-contexts-openai` package not found, "
            "please run `pip install lavague-contexts-openai`"
        )

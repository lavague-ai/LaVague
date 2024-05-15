from llama_index.core.llms import LLM
from llama_index.core.multi_modal_llms import MultiModalLLM
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core import PromptTemplate
from lavague.core.extractors import BaseExtractor
from lavague.core.retrievers import BaseHtmlRetriever

DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.0


class Context:
    """Set the context which will be used thourough the action generation pipeline."""

    def __init__(
        self,
        llm: LLM,
        mm_llm: MultiModalLLM,
        embedding: BaseEmbedding,
        retriever: BaseHtmlRetriever,
        prompt_template: PromptTemplate,
        extractor: BaseExtractor,
    ):
        """
        llm (`LLM`):
            The llm that will be used the generate the python code
        mm_llm (`MultiModalLLM`):
            The multimodal llm that will be used by the world model
        embedding: (`BaseEmbedding`)
            The embedder used by the retriever
        retriever (`BaseHtmlRetriever`)
            The retriever used to extract context from the html page
        prompt_template (`str`):
            The prompt_template given to the llm, later completed by chunks of the html page and the query
        cleaning_function (`Callable[[str], Optional[str]]`):
            Function to extract the python code from the llm output
        """
        self.llm = llm
        self.mm_llm = mm_llm
        self.embedding = embedding
        self.retriever = retriever
        self.prompt_template = prompt_template
        self.extractor = extractor


def get_default_context() -> Context:
    try:
        from lavague.contexts.openai import OpenaiContext

        return OpenaiContext()
    except ImportError:
        raise ImportError(
            "`lavague-contexts-openai` package not found, "
            "please run `pip install lavague-contexts-openai`"
        )

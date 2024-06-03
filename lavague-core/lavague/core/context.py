from llama_index.core.llms import LLM
from llama_index.core.multi_modal_llms import MultiModalLLM
from llama_index.core.embeddings import BaseEmbedding

DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.0


class Context:
    """Set the context which will be used thourough the action generation pipeline."""

    def __init__(
        self,
        llm: LLM,
        mm_llm: MultiModalLLM,
        embedding: BaseEmbedding,
    ):
        """
        llm (`LLM`):
            The llm that will be used the generate the python code
        mm_llm (`MultiModalLLM`):
            The multimodal llm that will be used by the world model
        embedding: (`BaseEmbedding`)
            The embedder used by the retriever
        """
        self.llm = llm
        self.mm_llm = mm_llm
        self.embedding = embedding


def get_default_context() -> Context:
    try:
        from lavague.contexts.openai import OpenaiContext

        return OpenaiContext()
    except ImportError:
        raise ImportError(
            "`lavague-contexts-openai` package not found, "
            "please run `pip install lavague-contexts-openai`"
        )

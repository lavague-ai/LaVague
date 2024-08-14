from lavague.core.context import Context
from llama_index.core.multi_modal_llms import MultiModalLLM
from typing import Optional
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.base import BaseLLM
from lavague.contexts.cache.llm_cache import LLMCache
from lavague.contexts.cache.mm_llm_cache import MultiModalLLMCache
from lavague.contexts.cache.embedding_cache import EmbeddingCache
from lavague.core.context import get_default_context


class ContextCache(Context):
    def __init__(
        self,
        llm_fallback: Optional[BaseLLM] = None,
        mm_llm_fallback: Optional[MultiModalLLM] = None,
        embedding_fallback: Optional[BaseEmbedding] = None,
    ) -> Context:
        return super().__init__(
            LLMCache(fallback=llm_fallback),
            MultiModalLLMCache(fallback=mm_llm_fallback),
            EmbeddingCache(fallback=embedding_fallback),
        )

    @classmethod
    def from_context(cls, context: Context) -> "ContextCache":
        return cls(
            llm_fallback=context.llm,
            mm_llm_fallback=context.mm_llm,
            embedding_fallback=context.embedding,
        )

    @classmethod
    def default(cls) -> "ContextCache":
        return cls.from_context(get_default_context())

from lavague.core.context import Context
from llama_index.core.multi_modal_llms import MultiModalLLM
from typing import Optional
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.base import BaseLLM
from lavague.contexts.cache.llm_cache import LLMCache
from lavague.contexts.cache.mm_llm_cache import MultiModalLLMCache
from lavague.contexts.cache.embedding_cache import EmbeddingCache


class ContextCache(Context):
    def __init__(
        self,
        llm_fallback: Optional[BaseLLM] = None,
        mm_llm_fallback: Optional[MultiModalLLM] = None,
        embedding_fallback: Optional[BaseEmbedding] = None,
        yml_prompts_file: str = "prompts.yml",
    ) -> Context:
        return super().__init__(
            LLMCache(
                fallback=llm_fallback,
                yml_prompts_file=yml_prompts_file,
            ),
            MultiModalLLMCache(
                fallback=mm_llm_fallback,
                yml_prompts_file=yml_prompts_file,
            ),
            EmbeddingCache(
                fallback=embedding_fallback, yml_prompts_file=yml_prompts_file
            ),
        )

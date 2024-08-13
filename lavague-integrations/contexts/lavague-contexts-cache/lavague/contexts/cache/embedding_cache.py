from llama_index.core.embeddings import (
    BaseEmbedding,
    MockEmbedding as LlamaMockEmbedding,
)
from llama_index.core.types import PydanticProgramMode
from lavague.contexts.cache.prompts_cache import PromptsCache
from typing import Dict, List, Optional, Callable


class EmbeddingCache(LlamaMockEmbedding, PromptsCache):
    """Embedding cache for test purpose. Don't use it for production, vector storage is not optimized"""

    fallback: Optional[BaseEmbedding]
    yml_prompts_file: Optional[str]
    dim_separator = ", "

    def __init__(
        self,
        prompts: Dict[str, str] = None,
        pydantic_program_mode: PydanticProgramMode = PydanticProgramMode.DEFAULT,
        fallback: Optional[BaseEmbedding] = None,
        yml_prompts_file: Optional[str] = None,
    ) -> None:
        LlamaMockEmbedding.__init__(
            self,
            embed_dim=1,
            pydantic_program_mode=pydantic_program_mode,
        )
        PromptsCache.__init__(
            self,
            prompts=prompts,
            yml_prompts_file=yml_prompts_file,
        )
        self.fallback = fallback

    def get_embedding(
        self, text: str, embedder: Callable[[str], List[float]]
    ) -> List[float]:
        value = self.get_for_prompt(text)

        if value is not None:
            return list(map(float, value.split(self.dim_separator)))

        if self.fallback is None:
            value = super()._get_vector()
        else:
            value = embedder(text)

        self.add_prompt(text, self.dim_separator.join(list(map(str, value))))
        return value

    def get_text_embedding(self, text: str) -> List[float]:
        return self.get_embedding(text, self.fallback.get_text_embedding)

    def get_query_embedding(self, query: str) -> List[float]:
        return self.get_embedding(query, self.fallback.get_query_embedding)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self.get_text_embedding(txt) for txt in texts]

    def _get_query_embeddings(self, queries: List[str]) -> List[List[float]]:
        return [self.get_query_embedding(txt) for txt in queries]

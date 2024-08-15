from llama_index.core.embeddings import (
    BaseEmbedding,
    MockEmbedding as LlamaMockEmbedding,
)
from lavague.contexts.cache.prompts_store import PromptsStore, VectorStrPromptStore
from typing import List, Optional, Callable
import sys


class EmbeddingCache(LlamaMockEmbedding):
    fallback: Optional[BaseEmbedding]
    store: PromptsStore[List[float]] = None
    max_dimensions: Optional[int]

    def __init__(
        self,
        fallback: Optional[BaseEmbedding] = None,
        yml_prompts_file: Optional[str] = "embeddings.yml",
        store: Optional[PromptsStore[List[float]]] = None,
        max_dimensions: Optional[int] = 10,
    ) -> None:
        super().__init__(embed_dim=max_dimensions)
        self.store = store or VectorStrPromptStore(yml_prompts_file=yml_prompts_file)
        self.fallback = fallback
        self.max_dimensions = max_dimensions

    def _reduce_dimension(self, value: List[float]):
        """Linear dimension reduction compressing last features, single-vector but less accurate than PCA or t-SNE"""
        while len(value) > self.max_dimensions:
            last_value = value.pop()
            value[-1] = value[-1] + last_value
            if value[-1] == float("inf"):
                value[-1] = sys.float_info.min + last_value
            elif value[-1] == float("-inf"):
                value[-1] = sys.float_info.max - last_value

    def get_embedding(
        self, text: str, embedder: Callable[[str], List[float]]
    ) -> List[float]:
        value = self.store.get_for_prompt(text)

        if value is not None:
            return value

        if self.fallback is None:
            value = super()._get_vector()
        else:
            value = embedder(text)
            self._reduce_dimension(value)

        self.store.add_prompt(text, value)
        return value

    def get_text_embedding(self, text: str) -> List[float]:
        return self.get_embedding(text, self.fallback.get_text_embedding)

    def get_query_embedding(self, query: str) -> List[float]:
        return self.get_embedding(query, self.fallback.get_query_embedding)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self.get_text_embedding(txt) for txt in texts]

    def _get_query_embeddings(self, queries: List[str]) -> List[List[float]]:
        return [self.get_query_embedding(txt) for txt in queries]

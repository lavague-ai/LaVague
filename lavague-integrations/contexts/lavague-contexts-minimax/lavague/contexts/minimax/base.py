from typing import Optional, List
from llama_index.llms.openai_like import OpenAILike
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.core.embeddings import BaseEmbedding
from pydantic import PrivateAttr
import os
import time
import requests
from lavague.core.context import Context, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE

MINIMAX_API_BASE = "https://api.minimax.io/v1"


class MiniMaxEmbedding(BaseEmbedding):
    """MiniMax embedding model using the embo-01 API."""

    _api_key: str = PrivateAttr()
    _api_base: str = PrivateAttr()

    def __init__(
        self,
        api_key: str,
        model_name: str = "embo-01",
        api_base: str = MINIMAX_API_BASE,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)
        self._api_key = api_key
        self._api_base = api_base

    def _call_api(
        self, texts: List[str], embed_type: str = "db", max_retries: int = 5
    ) -> List[List[float]]:
        for attempt in range(max_retries):
            response = requests.post(
                f"{self._api_base}/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.model_name, "texts": texts, "type": embed_type},
            )
            response.raise_for_status()
            data = response.json()
            base_resp = data.get("base_resp", {})
            status_code = base_resp.get("status_code", 0)
            if status_code == 0 and data.get("vectors") is not None:
                return data["vectors"]
            if status_code == 1002 and attempt < max_retries - 1:
                time.sleep(min(2 ** (attempt + 2), 30))
                continue
            if data.get("vectors") is None:
                msg = base_resp.get("status_msg", "Unknown error")
                raise RuntimeError(f"MiniMax embedding API error: {msg}")
        raise RuntimeError("MiniMax embedding API: max retries exceeded")

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._call_api([query], "query")[0]

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._call_api([text], "db")[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._call_api(texts, "db")

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)


class MiniMaxContext(Context):
    def __init__(
        self,
        api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        llm: str = "MiniMax-M2.7",
        mm_llm: str = "gpt-4o",
        embedding: str = "embo-01",
    ) -> Context:
        if api_key is None:
            api_key = os.getenv("MINIMAX_API_KEY")
            if api_key is None:
                raise ValueError("MINIMAX_API_KEY is not set")
        if openai_api_key is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key is None:
                raise ValueError(
                    "OPENAI_API_KEY is not set (required for multimodal support)"
                )
        return super().__init__(
            OpenAILike(
                api_key=api_key,
                api_base=MINIMAX_API_BASE,
                model=llm,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
                is_chat_model=True,
            ),
            OpenAIMultiModal(api_key=openai_api_key, model=mm_llm),
            MiniMaxEmbedding(api_key=api_key, model_name=embedding),
            OpenAILike(
                api_key=api_key,
                api_base=MINIMAX_API_BASE,
                model=llm,
                max_tokens=4096,
                temperature=DEFAULT_TEMPERATURE,
                is_chat_model=True,
            ),
        )

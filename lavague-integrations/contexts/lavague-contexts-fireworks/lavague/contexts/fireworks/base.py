from typing import Optional
from llama_index.llms.fireworks import Fireworks
from llama_index.embeddings.fireworks import FireworksEmbedding
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
import os
from lavague.core.context import Context, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE


class FireworksContext(Context):
    def __init__(
        self,
        api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        llm: str = "accounts/fireworks/models/llama-v3p1-70b-instruct",
        mm_llm: str = "gpt-4o",
        embedding: str = "nomic-ai/nomic-embed-text-v1.5",
    ) -> Context:
        if api_key is None:
            api_key = os.getenv("FIREWORKS_API_KEY")
            if api_key is None:
                raise ValueError("FIREWORKS_API_KEY is not set")
        if openai_api_key is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key == None:
                raise ValueError("OPENAI_API_KEY is not set")
        return super().__init__(
            Fireworks(
                model=llm,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
                api_key=api_key,
            ),
            OpenAIMultiModal(api_key=openai_api_key, model=mm_llm),
            FireworksEmbedding(api_key=api_key, model_name=embedding),
        )

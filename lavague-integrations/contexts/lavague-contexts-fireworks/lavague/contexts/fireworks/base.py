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
        llm: str = "models/llama-v3p1-405b-instruct",
        mm_llm: str = "gpt-4o",
    ) -> Context:
        if api_key is None:
            api_key = os.getenv("FIREWORKS_API_KEY")
            if api_key is None:
                raise ValueError("FIREWORKS_API_KEY is not set")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key == None:
            raise ValueError("OPENAI_API_KEY is not set")
        return super().__init__(
            Fireworks(
                model="accounts/fireworks/" + llm,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
            ),
            OpenAIMultiModal(api_key=openai_api_key, model=mm_llm),
            FireworksEmbedding(),
        )

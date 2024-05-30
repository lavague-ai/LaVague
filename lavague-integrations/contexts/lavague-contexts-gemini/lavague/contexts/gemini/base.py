from typing import Optional
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.multi_modal_llms.gemini import GeminiMultiModal
import os
from lavague.core.context import Context, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE


class GeminiContext(Context):
    def __init__(
        self,
        api_key: Optional[str] = None,
        llm: str = "models/gemini-1.5-flash-latest",
        mm_llm: str = "models/gemini-1.5-pro-latest",
        embedding: str = "models/text-embedding-004",
    ) -> Context:
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key is None:
                raise ValueError("GOOGLE_API_KEY is not set")
        return super().__init__(
            Gemini(
                api_key=api_key,
                model_name=llm,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
            ),
            GeminiMultiModal(api_key=api_key, model_name=mm_llm),
            GeminiEmbedding(api_key=api_key, model_name=embedding),
        )

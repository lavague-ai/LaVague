from typing import Optional
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.multi_modal_llms.anthropic import AnthropicMultiModal
import os
from lavague.core.context import Context, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE


class AnthropicContext(Context):
    def __init__(
        self,
        api_key: Optional[str] = None,
        llm: str = "claude-3-5-sonnet-20240620",
        mm_llm: str = "claude-3-5-sonnet-20240620",
        embedding: str = "text-embedding-3-small",
    ) -> Context:
        if api_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key is None:
                raise ValueError("ANTHROPIC_API_KEY is not set")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key == None:
            raise ValueError("OPENAI_API_KEY is not set")
        return super().__init__(
            Anthropic(
                model=llm,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
            ),
            AnthropicMultiModal(api_key=api_key, model=mm_llm),
            OpenAIEmbedding(api_key=openai_api_key),
        )

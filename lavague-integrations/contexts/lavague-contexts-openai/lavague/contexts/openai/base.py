from typing import Optional
from llama_index.llms.openai import OpenAI
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal
import os
from lavague.core.context import Context, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE


class OpenaiContext(Context):
    def __init__(
        self,
        api_key: Optional[str] = None,
        llm: str = "gpt-4o",
        mm_llm: str = "gpt-4o",
        embedding: str = "text-embedding-3-large",
    ) -> Context:
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError("OPENAI_API_KEY is not set")
        return super().__init__(
            OpenAI(
                api_key=api_key,
                model=llm,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
            ),
            OpenAIMultiModal(api_key=api_key, model=mm_llm),
            OpenAIEmbedding(api_key=api_key, model=embedding),
        )


class AzureOpenaiContext(Context):
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        llm: Optional[str] = None,
        mm_llm: Optional[str] = None,
        embedding: BaseEmbedding = OpenAIEmbedding(model="text-embedding-3-large"),
    ):
        if api_key is None:
            api_key = os.getenv("AZURE_OPENAI_KEY")
        if endpoint is None:
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if deployment is None:
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        return super().__init__(
            AzureOpenAI(
                model=llm, api_key=api_key, endpoint=endpoint, deployment=deployment
            ),
            AzureOpenAIMultiModal(
                model=mm_llm, api_key=api_key, endpoint=endpoint, deployment=deployment
            ),
            embedding,
        )

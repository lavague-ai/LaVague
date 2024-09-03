from typing import Optional
from llama_index.llms.openai import OpenAI
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
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
            OpenAI(
                api_key=api_key,
                model=llm,
                max_tokens=4096,
                temperature=DEFAULT_TEMPERATURE,
            ),
        )


class AzureOpenaiContext(Context):
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        llm: str = "got-4o",
        mm_llm: str = "got-4o",
        mm_llm_endpoint: Optional[str] = None,
        mm_llm_deployment: Optional[str] = None,
        embedding: str = "text-embedding-3-small",
        embedding_deployment: Optional[str] = None,
        embedding_endpoint: Optional[str] = None,
        api_version: str = "2023-07-01-preview",
    ):
        if api_key is None:
            api_key = os.getenv("AZURE_OPENAI_KEY")
            if api_key is None:
                raise ValueError("AZURE_OPENAI_API_KEY is not set")
        if endpoint is None:
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            if endpoint is None:
                raise ValueError("AZURE_OPENAI_ENDPOINT is not set")
        if deployment is None:
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
            if deployment is None:
                raise ValueError("AZURE_OPENAI_DEPLOYMENT is not set")
        if embedding_deployment is None:
            raise ValueError("No embedding_deployment argument passed")
        if embedding_endpoint is None:
            embedding_endpoint = endpoint
        if mm_llm_deployment is None:
            mm_llm_deployment = deployment
        if mm_llm_endpoint is None:
            mm_llm_endpoint = endpoint
        return super().__init__(
            AzureOpenAI(
                api_key=api_key,
                model=llm,
                deployment_name=deployment,
                azure_endpoint=endpoint,
                api_version=api_version,
            ),
            AzureOpenAIMultiModal(
                api_key=api_key,
                model=mm_llm,
                deployment_name=mm_llm_deployment,
                azure_endpoint=mm_llm_endpoint,
                api_version=api_version,
            ),
            AzureOpenAIEmbedding(
                api_key=api_key,
                model=embedding,
                azure_endpoint=embedding_endpoint,
                deployment_name=embedding_deployment,
                api_version=api_version,
            ),
        )

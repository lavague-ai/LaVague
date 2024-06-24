from typing import Optional
from lavague.core.base_driver import BaseDriver
from lavague.core.retrievers import BaseHtmlRetriever, OpsmSplitRetriever
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
import os
from lavague.core.context import Context, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE


class LocalContext(Context):
    def __init__(
        self,
        api_key: Optional[str] = None,
        llm: str = "meta-llama/Meta-Llama-3-8B-Instruct",
        mm_llm: str = "gpt-4o",
        embedding: str = "BAAI/bge-small-en-v1.5",
        driver: BaseDriver = None,
        retriever: BaseHtmlRetriever = None,
    ) -> Context:
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError("OPENAI_API_KEY is not set")
        if driver is None:
            from lavague.drivers.selenium.base import SeleniumDriver

            driver = SeleniumDriver()
        if retriever is None:
            retriever = OpsmSplitRetriever(
                driver, HuggingFaceEmbedding(model_name=embedding)
            )
        return super().__init__(
            HuggingFaceLLM(
                model_name=llm,
                max_new_tokens=DEFAULT_MAX_TOKENS,
                generate_kwargs={"temperature": DEFAULT_TEMPERATURE}
            ),
            OpenAIMultiModal(api_key=api_key, model=mm_llm),
            retriever,
            driver,
        )

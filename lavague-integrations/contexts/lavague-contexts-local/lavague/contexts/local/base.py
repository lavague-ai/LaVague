from typing import Optional
from lavague.core.base_driver import BaseDriver
from lavague.core.retrievers import BaseHtmlRetriever, OpsmSplitRetriever
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
import os
import torch
from transformers import AutoTokenizer
from lavague.core.context import Context, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE
import torch
from transformers import AutoTokenizer

class LocalContext(Context):
    def __init__(
        self,
        api_key: Optional[str] = None,
        llm: str = "meta-llama/Meta-Llama-3-8B-Instruct",
        mm_llm: str = "gpt-4o",
        embedding: str = "BAAI/bge-small-en-v1.5",
        hf_api_key: Optional[str] = None,
        driver: BaseDriver = None,
        retriever: BaseHtmlRetriever = None,
    ) -> Context:
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError("OPENAI_API_KEY is not set")
        if hf_api_key is None:
            hf_api_key = os.getenv("HUGGING_FACE_HUB_TOKEN")
            if hf_api_key is None:
                raise ValueError("HUGGING_FACE_HUB_TOKEN is not set")
        if driver is None:
            from lavague.drivers.selenium.base import SeleniumDriver

            driver = SeleniumDriver()
        if retriever is None:
            retriever = OpsmSplitRetriever(
                driver, HuggingFaceEmbedding(model_name=embedding), top_k=2
            )
        tokenizer = AutoTokenizer.from_pretrained(
            llm,
            token=hf_api_key,
        )
        stopping_ids = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|eot_id|>"),
        ]
        return super().__init__(
            HuggingFaceLLM(
                model_name=llm,
                model_kwargs={
                    "token": hf_api_key,
                    "torch_dtype": torch.bfloat16,
                },
                generate_kwargs={
                    "do_sample": True,
                    "temperature": 0.6,
                    "top_p": 0.9,
                },
                tokenizer_name=llm,
                tokenizer_kwargs={"token": hf_api_key},
                stopping_ids=stopping_ids,
            ),
            OpenAIMultiModal(api_key=api_key, model=mm_llm),
            retriever,
            driver,
        )

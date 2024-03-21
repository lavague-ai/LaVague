
import os

DEFAULT_LLM = "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO"
DEFAULT_MAX_NEW_TOKENS = 512

from llama_index.llms.openai import OpenAI

class LLM(OpenAI):
    def __init__(self):
        max_new_tokens = 512
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        else:
            super().__init__(api_key=api_key, max_tokens=max_new_tokens)
            
from llama_index.llms.openai import OpenAI
from .. import MAX_TOKENS, TEMPERATURE

class OpenAIForAction(OpenAI):
    def __init__(self, api_key: str = None):
        """if api_key is none, llama-index will try to take it from the env"""
        super().__init__(
            api_key=api_key,
            max_tokens=512,
            temperature=0.0
        )
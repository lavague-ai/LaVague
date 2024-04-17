import os
from llama_index.llms.openai import OpenAI

class LLM(OpenAI):
    def __init__(self):
        max_new_tokens = 512
        api_key = os.getenv("OPENAI_API_KEY")
        super().__init__(
            api_key=api_key, max_tokens=max_new_tokens, temperature=0.0
        )

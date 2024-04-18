import os
from llama_index.llms.openai import OpenAI
from lavague.defaults import default_get_playwright_driver
from lavague.prompts import PLAYWRIGHT_PROMPT


class LLM(OpenAI):
    def __init__(self):
        max_new_tokens = 512
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        else:
            super().__init__(
                api_key=api_key, max_tokens=max_new_tokens, temperature=0.0
            )


get_driver = default_get_playwright_driver

prompt_template = PLAYWRIGHT_PROMPT

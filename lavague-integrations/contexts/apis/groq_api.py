from llama_index.llms.groq import Groq
from .. import MAX_TOKENS, TEMPERATURE

class GroqForAction(Groq):
    def __init__(self, api_key, model: str = "llama3-70b-8192"):
        super().__init__(
            api_key=api_key,
            model=model,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
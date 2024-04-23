import os
from llama_index.llms.groq import Groq


class LLM(Groq):
    # This class initializes the Groq API with selected models.
    # Available models: llama3-8b-8192, llama3-70b-8192, llama2-70b-4096, mixtral-8x7b-32768, gemma-7b-it
    def __init__(
            self,
            model: str = "llama3-70b-8192",
            api_key: str = os.getenv("GROQ_API_KEY"),
    ):
        if api_key is None:
            raise ValueError("GROQ_API_KEY environment variable is not set")

        super().__init__(
            model=model,
            api_key=api_key,
        )

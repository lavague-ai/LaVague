import os
from llama_index.llms.anthropic import Anthropic


class LLM(Anthropic):
    # This class initializes the Anthropic API with selected models.
    # Available models: claude-3-haiku-20240307, claude-3-sonnet-20240229, claude-3-opus-20240229
    def __init__(
            self,
            model: str = "claude-3-haiku-20240307",
            api_key: str = os.getenv("ANTHROPIC_API_KEY"),
    ):
        if api_key is None:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

        super().__init__(
            model=model,
            api_key=api_key,
        )
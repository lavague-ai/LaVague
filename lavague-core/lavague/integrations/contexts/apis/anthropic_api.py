from llama_index.llms.anthropic import Anthropic
from .. import MAX_TOKENS, TEMPERATURE

class AnthropicForAction(Anthropic):
    # This class initializes the Anthropic API with selected models.
    # Available models: claude-3-haiku-20240307, claude-3-sonnet-20240229, claude-3-opus-20240229
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        super().__init__(
            api_key=api_key,
            model=model,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
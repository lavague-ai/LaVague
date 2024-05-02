from llama_index.llms.litellm import LiteLLM
from .. import MAX_TOKENS, TEMPERATURE

class LiteLLMForAction(LiteLLM):
    """
    LiteLLM supports 100+ LLM APIs. See the complete list: https://docs.litellm.ai/docs/providers
    Since the api_key would depend on which provider is chosen, we do not hardcode reading a specific key from os env var.
    """

    def __init__(self, model: str = "gpt-3.5-turbo", **kwargs): 
        super().__init__(
            model=model,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            kwargs=kwargs,
        )
from llama_index.llms.litellm import LiteLLM


class LLM(LiteLLM):
    """
    LiteLLM supports 100+ LLM APIs. See the complete list: https://docs.litellm.ai/docs/providers
    Since the api_key would depend on which provider is chosen, we do not hardcode reading a specific key from os env var.
    """

    def __init__(self, model="gpt-3.5-turbo", **kwargs):
        default_max_new_tokens = 512
        super().__init__(
            model=model,
            max_tokens=default_max_new_tokens,
            temperature=0.0,
            kwargs=kwargs,
        )

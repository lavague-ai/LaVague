from llama_index.llms.openai import OpenAI
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.llms.huggingface import HuggingFaceInferenceAPI
from llama_index.core.base.llms.types import CompletionResponse
from llama_index.llms.litellm import LiteLLM

from .config import get_config

_config = get_config()

def stream_complete(self, prompt: str, **kwargs):
    def gen():
        # patch the patch, on some versions the caller tries to pass the formatted keyword, which doesn't exist
        kwargs.pop("formatted", None)
        text = ""
        for x in self._sync_client.text_generation(
            prompt, **{**{"max_new_tokens": self.num_output, "stream": True}, **kwargs}
        ):
            text += x
            yield CompletionResponse(text=text, delta=x)

    return gen()


HuggingFaceInferenceAPI.stream_complete = stream_complete


class OpenAILLM(OpenAI):
    def __init__(self):
        max_new_tokens = 512
        api_key = _config['openai_api']['api_key']
        if api_key is None:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        else:
            super().__init__(api_key=api_key, max_tokens=max_new_tokens)

class AzureOpenAILLM(AzureOpenAI):
    def __init__(self):
        super().__init__(
            model=_config['azure_openai']['model'],
            deployment_name=_config['azure_openai']['deployment_name'],
            api_key=_config['azure_openai']['api_key'],
            azure_endpoint=_config['azure_openai']['azure_endpoint'],
            api_version=_config['azure_openai']['api_version'],
            temperature=0.0,
        )

class HuggingFaceLLM(HuggingFaceInferenceAPI):
    def __init__(self):
        token = _config['huggingface']['auth_token']

        if token is None:
            raise ValueError("HF_TOKEN environment variable is not set")
        else:
            super().__init__(
                model_name=_config['huggingface']['inference']['mixtral']['api_llm'],
                token=token,
                num_output=_config['huggingface']['inference']['mixtral']['default_max_new_tokens'],
            )

class OpenAILiteLLM(LiteLLM):
    """
    LiteLLM supports 100+ LLM APIs. See the complete list: https://docs.litellm.ai/docs/providers
    Since the api_key would depend on which provider is chosen, we do not hardcode reading a specific key from os env var.
    """

    def __init__(self, model=_config['litellm']['model'], **kwargs):
        default_max_new_tokens = _config['litellm']['default_max_new_tokens']
        super().__init__(
            model=model,
            max_tokens=default_max_new_tokens,
            temperature=0.0,
            kwargs=kwargs,
        )
from llama_index.llms.azure_openai import AzureOpenAI
from .. import MAX_TOKENS, TEMPERATURE

class AzureOpenAIForAction(AzureOpenAI):
    def __init__(self, azure_endpoint: str, api_key: str, api_version: str, deployment_name: str, model: str):
        super().__init__(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version,
            deployment_name=deployment_name,
            model=model,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
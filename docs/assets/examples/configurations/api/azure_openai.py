import os
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

api_key = os.getenv("AZURE_OPENAI_KEY")
api_version = "2023-05-15"
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model = "gpt-4"
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-turbo")

# Temporarily use local embed model to avoid dependency on new OpenAI API default model - to change later
LOCAL_EMBED_MODEL = "BAAI/bge-small-en-v1.5"


class Embedder(HuggingFaceEmbedding):
    def __init__(self, model_name: str = LOCAL_EMBED_MODEL, device: str = "cuda"):
        super().__init__(model_name, device)


class LLM(AzureOpenAI):
    def __init__(self):
        super().__init__(
            model=model,
            deployment_name=deployment_name,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            temperature=0.0,
        )

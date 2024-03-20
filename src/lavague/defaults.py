from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM
from transformers import AutoTokenizer, AutoModelForCausalLM
from llama_index.llms.huggingface import HuggingFaceInferenceAPI
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core.base.llms.types import CompletionResponse
from dotenv import load_dotenv
import os

load_dotenv()

DEFAULT_EMBED_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_LOCAL_LLM = "HuggingFaceH4/zephyr-7b-gemma-v0.1"
HUGGINGFACE_API_LLM = "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO"
DEFAULT_MAX_NEW_TOKENS = 512
HF_TOKEN = os.getenv("HF_TOKEN", "")

class DefaultEmbedder(HuggingFaceEmbedding):
    def __init__(self, model_name: str = DEFAULT_EMBED_MODEL, device: str = "cuda"):
        super().__init__(model_name, device)


class DefaultLocalLLM(HuggingFaceLLM):
    def __init__(
        self,
        model_name: str = DEFAULT_LOCAL_LLM,
        max_new_tokens: str = DEFAULT_MAX_NEW_TOKENS,
        quantization_config: dict = None,
    ):
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name, device_map="auto", quantization_config=quantization_config
        )

        super().__init__(
            model=model, tokenizer=tokenizer, max_new_tokens=max_new_tokens
        )


# Monkey patch because stream_complete is not implemented in the current version of llama_index
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

class HuggingfaceApiLLM(HuggingFaceInferenceAPI):
    def __init__(
        self,
        model_name: str = HUGGINGFACE_API_LLM,
        token: str = HF_TOKEN,
        num_output: str = DEFAULT_MAX_NEW_TOKENS,
    ):
        super().__init__(model_name=model_name, token=token, num_output=num_output)

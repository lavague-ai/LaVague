from llama_index.core.base.llms.types import CompletionResponse
from llama_index.llms.huggingface import HuggingFaceInferenceAPI
import os

DEFAULT_MAX_NEW_TOKENS = 512
HUGGINGFACE_API_LLM = "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO"

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

class LLM(HuggingFaceInferenceAPI):
    def __init__(self):
        token = os.getenv("HF_TOKEN")
        if token is None:
            raise ValueError("HF_TOKEN environment variable is not set")
        else:
            super().__init__(model_name=HUGGINGFACE_API_LLM, token=token, num_output=DEFAULT_MAX_NEW_TOKENS)
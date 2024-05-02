from llama_index.core.base.llms.types import CompletionResponse
from llama_index.llms.huggingface import HuggingFaceInferenceAPI
from .. import MAX_TOKENS

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

class HuggingFaceAPIForAction(HuggingFaceInferenceAPI):
    def __init__(self, token: str, model_name: str = "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO"):
        super().__init__(
            token=token,
            model_name=model_name,
            num_output=MAX_TOKENS,
        )
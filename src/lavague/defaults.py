from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from llama_index.llms.huggingface import HuggingFaceInferenceAPI
from llama_index.core.base.llms.types import CompletionResponse
from dotenv import load_dotenv
import os
import torch

load_dotenv()

DEFAULT_EMBED_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_LOCAL_LLM = "HuggingFaceH4/zephyr-7b-gemma-v0.1"
DEFAULT_LLM = "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO"
DEFAULT_MAX_NEW_TOKENS = 512
HF_TOKEN = os.environ["HF_TOKEN"]

# DEFAULT_QUANTIZATION_CONFIG = BitsAndBytesConfig(
# load_in_4bit=True,
# bnb_4bit_use_double_quant=True,
# bnb_4bit_quant_type="nf4",
# bnb_4bit_compute_dtype=torch.bfloat16
# )

class DefaultEmbedder(HuggingFaceEmbedding):
	def __init__(self, model_name=DEFAULT_EMBED_MODEL, device="cuda"):
		super().__init__(model_name, device)

class DefaultLocalLLM(HuggingFaceLLM):
	def __init__(self, model_name=DEFAULT_LOCAL_LLM, max_new_tokens=DEFAULT_MAX_NEW_TOKENS, quantization_config=None):
		tokenizer = AutoTokenizer.from_pretrained(model_name)
		model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", quantization_config=quantization_config)

		# We will stop generation as soon as the model outputs the end of Markdown to make inference faster
		stop_token_id = [tokenizer.convert_tokens_to_ids("```"), tokenizer.convert_tokens_to_ids("``")]
		super().__init__(model=model, tokenizer=tokenizer, max_new_tokens=max_new_tokens, stopping_ids=stop_token_id)

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

class DefaultLLM(HuggingFaceInferenceAPI):
	def __init__(self, model_name = DEFAULT_LLM, token=HF_TOKEN, num_output=DEFAULT_MAX_NEW_TOKENS):
		super().__init__(model_name=model_name, token=token, num_output=num_output)

from lavague.prompts import SELENIUM_GEMMA_PROMPT
from transformers import BitsAndBytesConfig
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(load_in_4bit=True)
model_id = "deepseek-ai/deepseek-coder-6.7b-instruct"
LOCAL_EMBED_MODEL = "BAAI/bge-small-en-v1.5"


class LLM(HuggingFaceLLM):
    def __init__(self):
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id, device_map="auto", quantization_config=quantization_config
        )

        model_kwargs = {
            "temperature": 0.0,
        }
        max_new_tokens = 1024

        # We will stop generation as soon as the model outputs the end of Markdown to make inference faster
        stop_token_id = [
            tokenizer.convert_tokens_to_ids("---"),
            tokenizer.convert_tokens_to_ids("```"),
        ]

        super().__init__(
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=max_new_tokens,
            stopping_ids=stop_token_id,
            model_kwargs=model_kwargs,
        )


class Embedder(HuggingFaceEmbedding):
    def __init__(self, model_name: str = LOCAL_EMBED_MODEL, device: str = "cuda"):
        super().__init__(model_name, device)


# We needed to steer the model more with a more explicit prompt so we use a custom prompt
prompt_template = SELENIUM_GEMMA_PROMPT

# The cleaning is also different in this case
cleaning_function = lambda code: code.split("```")[0]

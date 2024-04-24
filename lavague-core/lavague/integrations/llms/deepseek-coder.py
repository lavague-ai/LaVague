from transformers import BitsAndBytesConfig
from llama_index.llms.huggingface import HuggingFaceLLM
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from . import MAX_TOKENS, TEMPERATURE
from ...prompt_templates import SELENIUM_GEMMA_PROMPT_TEMPLATE

quantization_config = BitsAndBytesConfig(load_in_4bit=True)
model_id = "deepseek-ai/deepseek-coder-6.7b-instruct"
LOCAL_EMBED_MODEL = "BAAI/bge-small-en-v1.5"


class DeepSeekCoderForAction(HuggingFaceLLM):
    def __init__(self):
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id, device_map="auto", quantization_config=quantization_config
        )

        model_kwargs = {
            "temperature": TEMPERATURE,
        }

        # We will stop generation as soon as the model outputs the end of Markdown to make inference faster
        stop_token_id = [
            tokenizer.convert_tokens_to_ids("---"),
            tokenizer.convert_tokens_to_ids("```"),
        ]

        super().__init__(
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=MAX_TOKENS,
            stopping_ids=stop_token_id,
            model_kwargs=model_kwargs,
        )


# We needed to steer the model more with a more explicit prompt so we use a custom prompt
prompt_template = SELENIUM_GEMMA_PROMPT_TEMPLATE



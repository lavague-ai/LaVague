from llama_index.llms.huggingface import HuggingFaceLLM
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from lavague.core.action_context import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE

class ActionHuggingFaceLLM(HuggingFaceLLM):
    def __init__(
            self,
            model_id: str = "deepseek-ai/deepseek-coder-6.7b-instruct",
            quantization_config: BitsAndBytesConfig = BitsAndBytesConfig(load_in_4bit=True),
            max_tokens: int = DEFAULT_MAX_TOKENS,
            temperature: int = DEFAULT_TEMPERATURE,
        ):

        model = AutoModelForCausalLM.from_pretrained(
            model_id, device_map="auto", quantization_config=quantization_config
        )
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        # We will stop generation as soon as the model outputs the end of Markdown to make inference faster
        stop_token_id = [
            tokenizer.convert_tokens_to_ids("---"),
            tokenizer.convert_tokens_to_ids("```"),
        ]

        super().__init__(
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=max_tokens,
            stopping_ids=stop_token_id,
            model_kwargs={"temperature": temperature},
        )
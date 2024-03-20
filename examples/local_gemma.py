from lavague import CommandCenter, ActionEngine
from lavague.prompts import GEMMA_PROMPT
from transformers import BitsAndBytesConfig
from torch import bfloat16
import os.path
from llama_index.llms.huggingface import HuggingFaceLLM
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
from lavague.defaults import DefaultEmbedder

homedir = os.path.expanduser("~")

# Beware, if you don't have a nvidia GPU, this quantization config won't work
# To check if you have one configured correctly, you can run python -m bitsandbytes in your terminal

model_id = "HuggingFaceH4/zephyr-7b-gemma-v0.1"

quantization_config = BitsAndBytesConfig(load_in_8bit=True)

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", quantization_config=quantization_config)

model_kwargs = {
    "temperature": 0.0,
}

# We will stop generation as soon as the model outputs the end of Markdown to make inference faster
stop_token_id = [tokenizer.convert_tokens_to_ids("---"), tokenizer.convert_tokens_to_ids("```")]
llm = HuggingFaceLLM(model=model, tokenizer=tokenizer, max_new_tokens=1024,
                     stopping_ids=stop_token_id, model_kwargs=model_kwargs)

# We needed to steer the model more with a more explicit prompt
prompt_template = GEMMA_PROMPT

cleaning_function = lambda code: code.split("```")[0]
commandCenter = CommandCenter(
    ActionEngine(
        llm,
        DefaultEmbedder(),
        GEMMA_PROMPT,
        cleaning_function=cleaning_function,
    ),
    chromePath=f"{homedir}/chrome-linux64/chrome",
    chromedriverPath=f"{homedir}/chromedriver-linux64/chromedriver",
)
commandCenter.run(
    "https://huggingface.co",
    [
        "Click on the Datasets item on the menu, between Models and Spaces",
        "Click on the search bar 'Filter by name', type 'The Stack', and press 'Enter'",
        "Scroll by 500 pixels",
    ],
)

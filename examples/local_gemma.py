from lavague import CommandCenter, ActionEngine
from lavague.defaults import DefaultLocalLLM, DefaultEmbedder
from lavague.prompts import GEMMA_PROMPT
from transformers import BitsAndBytesConfig
from torch import bfloat16
import os.path

homedir = os.path.expanduser("~")

# Beware, if you don't have a nvidia GPU, this quantization config won't work
# To check if you have one configured correctly, you can run python -m bitsandbytes in your terminal

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=bfloat16,
)

commandCenter = CommandCenter(
    ActionEngine(
        DefaultLocalLLM(quantization_config=quantization_config),
        DefaultEmbedder(),
        GEMMA_PROMPT,
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

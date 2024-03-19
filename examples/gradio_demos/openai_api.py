from lavague import ActionEngine, CommandCenter
from lavague.defaults import AzureOpenAILLM, DefaultEmbedder
from lavague.prompts import DEFAULT_PROMPT
import os.path

homedir = os.path.expanduser("~")

commandCenter = CommandCenter(
    ActionEngine(AzureOpenAILLM(), DefaultEmbedder(), DEFAULT_PROMPT),
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
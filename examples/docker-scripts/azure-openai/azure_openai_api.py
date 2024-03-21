from lavague import ActionEngine, CommandCenter
from lavague.defaults import DefaultEmbedder
import os.path

homedir = os.path.expanduser("~")

import os
from llama_index.llms.azure_openai import AzureOpenAI

api_key=os.getenv("AZURE_OPENAI_KEY")
api_version="2023-05-15"
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model = "gpt-4"
deployment_name = "gpt-4-turbo"

llm = AzureOpenAI(
    model=model,
    deployment_name=deployment_name,
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
    temperature=0.0
)

commandCenter = CommandCenter(
    ActionEngine(
        llm,
        DefaultEmbedder(),
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

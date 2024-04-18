from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.llms.huggingface import HuggingFaceInferenceAPI
from llama_index.core.base.llms.types import CompletionResponse
from llama_index.llms.litellm import LiteLLM
from .driver import SeleniumDriver
from .prompts import DEFAULT_PROMPT
import os
from typing import Optional
from dotenv import load_dotenv
import re

from .config import get_config

load_dotenv()

_config = get_config()

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

class DefaultEmbedder(OpenAIEmbedding):
    def __init__(self, model="text-embedding-3-large"):
        super().__init__(model=model)


class DefaultLLM(OpenAI):
    def __init__(self):
        max_new_tokens = 512
        api_key = _config['openai_api']['api_key']
        if api_key is None:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        else:
            super().__init__(api_key=api_key, max_tokens=max_new_tokens)

class AzureOpenAILLM(AzureOpenAI):
    def __init__(self):
        super().__init__(
            model=_config['azure_openai']['model'],
            deployment_name=_config['azure_openai']['deployment_name'],
            api_key=_config['azure_openai']['api_key'],
            azure_endpoint=_config['azure_openai']['azure_endpoint'],
            api_version=_config['azure_openai']['api_version'],
            temperature=0.0,
        )

class HuggingFaceLLM(HuggingFaceInferenceAPI):
    def __init__(self):
        token = _config['huggingface']['auth_token']

        if token is None:
            raise ValueError("HF_TOKEN environment variable is not set")
        else:
            super().__init__(
                model_name=_config['huggingface']['inference']['mixtral']['api_llm'],
                token=token,
                num_output=_config['huggingface']['inference']['mixtral']['default_max_new_tokens'],
            )

class OpenAILiteLLM(LiteLLM):
    """
    LiteLLM supports 100+ LLM APIs. See the complete list: https://docs.litellm.ai/docs/providers
    Since the api_key would depend on which provider is chosen, we do not hardcode reading a specific key from os env var.
    """

    def __init__(self, model=_config['litellm']['model'], **kwargs):
        default_max_new_tokens = _config['litellm']['default_max_new_tokens']
        super().__init__(
            model=model,
            max_tokens=default_max_new_tokens,
            temperature=0.0,
            kwargs=kwargs,
        )

def default_python_code_extractor(markdown_text: str) -> Optional[str]:
    # Pattern to match the first ```python ``` code block
    pattern = r"```python(.*?)```"

    # Using re.DOTALL to make '.' match also newlines
    match = re.search(pattern, markdown_text, re.DOTALL)
    if match:
        # Return the first matched group, which is the code inside the ```python ```
        return match.group(1).strip()
    else:
        # Return None if no match is found
        return None


def default_get_driver() -> SeleniumDriver:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.keys import Keys
    import os.path

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1600,900")

    homedir = os.path.expanduser("~")

    # Paths to the chromedriver files
    path_linux = f"{homedir}/chromedriver-linux64/chromedriver"
    path_testing = f"{homedir}/chromedriver-testing/chromedriver"
    path_mac = "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

    # To avoid breaking change kept legacy linux64 path
    if os.path.exists(path_linux):
        chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
        webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")
    elif os.path.exists(path_testing):
        if os.path.exists(f"{homedir}/chrome-testing/{path_mac}"):
            chrome_options.binary_location = f"{homedir}/chrome-testing/{path_mac}"
        # Can add support here for other chrome binaries with else if statements
        webdriver_service = Service(f"{homedir}/chromedriver-testing/chromedriver")
    else:
        raise FileNotFoundError("Neither chromedriver file exists.")

    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    return SeleniumDriver(driver)


def defaultTestCode() -> str:
    return 'driver.execute_script("window.scrollBy(0, 500)")'

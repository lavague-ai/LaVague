from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from .driver import SeleniumDriver
from dotenv import load_dotenv

load_dotenv()

DEFAULT_EMBED_MODEL = "BAAI/bge-small-en-v1.5"


class DefaultEmbedder(HuggingFaceEmbedding):
    def __init__(self, model_name: str = DEFAULT_EMBED_MODEL, device: str = "cuda"):
        super().__init__(model_name, device)


from llama_index.llms.openai import OpenAI
import os


class DefaultLLM(OpenAI):
    def __init__(self):
        max_new_tokens = 512
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        else:
            super().__init__(api_key=api_key, max_tokens=max_new_tokens)


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
    chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
    webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")

    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    return SeleniumDriver(driver)

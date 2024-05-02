import os
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from lavague.driver import SeleniumDriver

api_key = os.getenv("AZURE_OPENAI_KEY")
api_version = "2024-02-15-preview"
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model = "gpt-35-turbo"
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")

LOCAL_EMBED_MODEL = "BAAI/bge-small-en-v1.5"

class Embedder(HuggingFaceEmbedding):
    def __init__(self, model_name: str = LOCAL_EMBED_MODEL, device: str = "cuda"):
        super().__init__(model_name, device)


class LLM(AzureOpenAI):
    def __init__(self):
        super().__init__(
            model=model,
            deployment_name=deployment_name,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            temperature=0.0,
        )

def get_driver() -> SeleniumDriver:
        """Extra options to make the driver more static for evaluation purposes."""
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
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.javascript": 2
        })
        chrome_options.add_argument('--proxy-server=127.0.0.1:9999')

        homedir = os.path.expanduser("~")

        # Paths to the chromedriver files
        path_linux = f"{homedir}/chromedriver-linux64/chromedriver"
        path_testing = f"{homedir}/chromedriver-testing/chromedriver"
        path_mac = (
            "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
        )

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

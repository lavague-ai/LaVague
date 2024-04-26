from llama_index.core.base.llms.types import CompletionResponse
from llama_index.llms.huggingface import HuggingFaceInferenceAPI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM
import os

from lavague.driver import SeleniumDriver

DEFAULT_MAX_NEW_TOKENS = 512
HUGGINGFACE_API_LLM = "meta-llama/Meta-Llama-3-8B-Instruct"

# Mokey patch because stream_complete is not implemented in the current version of llama_index
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

class LLM(HuggingFaceInferenceAPI):
    def __init__(self):
        token = os.getenv("HF_TOKEN")
        if token is None:
            raise ValueError("HF_TOKEN environment variable is not set")
        else:
            super().__init__(
                model_name=HUGGINGFACE_API_LLM,
                token=token,
                num_output=DEFAULT_MAX_NEW_TOKENS,
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
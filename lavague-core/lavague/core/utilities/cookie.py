from lavague.core.base_driver import BaseDriver
from lavague.core.navigation import NavigationEngine
from llama_index.core.multi_modal_llms import MultiModalLLM
from pathlib import Path
from llama_index.core import SimpleDirectoryReader

COOKIE_BANNER_DETECTION_PROMPT = """You are an AI system whose role is to detect and handle cookie banners.

Your primary goal is to identify if there is a cookie banner present on the page and provide instructions on how to accept the cookies.

## Instructions:

1. Carefully examine the screenshot for any cookie banners or consent popups.
2. Describe your thiking process to assess if a cookie banner is present. If so provide clear instructions on how to accept the cookies. Focus on accepting all cookies rather than customizing settings.

## Output Format:

Your output should be in the following format:

- Description: [Brief description of the cookie banner if present, or the main content of the webpage if no banner is present]
- Cookie Banner: [Yes/No]
- Instruction: [Clear instruction on how to accept cookies if a banner is present, or "N/A" if no banner is detected]

## Examples:

Description: A cookie consent popup is overlaying the content at the bottom of the page, with "Accept all cookies" and "More options" buttons visible.
Cookie Banner: Yes
Instruction: Click on "Accept all cookies"
---
Description: The webpage displays a product catalog for industrial hoses. No cookie banner is visible.
Cookie Banner: No
Instruction: N/A
---
Description: A large cookie notice is displayed at the top of the page, covering most of the content. It includes options to "Accept necessary cookies only" and "Accept all cookies".
Cookie Banner: Yes
Instruction: Click on "Accept all cookies"
---

Here is the next example to handle:
Description:
Cookie Banner:
Instruction:
"""

class CookieAccepter:
    def __init__(self, driver: BaseDriver, mm_llm: MultiModalLLM, navigation_engine: NavigationEngine):
        self.driver = driver
        self.mm_llm = mm_llm
        self.navigation_engine = navigation_engine

    def _is_cookie_banner_present(self):
        cookie_folder = Path("cookie_banners")
        # If folder does not exist, create it
        if not cookie_folder.exists():
            cookie_folder.mkdir()

        # If the folder is non empty, clear it
        for file in cookie_folder.iterdir():
            file.unlink()

        self.driver.save_screenshot(cookie_folder)
        image_documents = SimpleDirectoryReader("cookie_banners").load_data()
        response = self.mm_llm.complete(COOKIE_BANNER_DETECTION_PROMPT, image_documents=image_documents).text

        is_cookie_banner_present = response.split("Cookie Banner: ")[-1].split("\n")[0].strip() == "Yes"
        instruction = response.split("Instruction: ")[-1].strip()

        return is_cookie_banner_present, instruction

    def accept_cookies(self):
        is_cookie_banner_present, instruction = self._is_cookie_banner_present()

        while is_cookie_banner_present:
            try:
                self.navigation_engine.execute_instruction(instruction)

            # TODO: Better handling of this exception that arises because of implementation of logger that raise an exception when navigation engine is used without agent call (logger AttributeError: 'AgentLogger' object has no attribute 'current_row')
            except AttributeError:
                pass
            except Exception as e:
                print(f"Error: {e}")
                break

            is_cookie_banner_present, instruction = self._is_cookie_banner_present()
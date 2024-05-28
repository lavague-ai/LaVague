import hashlib
import os
from pathlib import Path
import time
from typing import Any, Optional, Callable
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from lavague.core.base_driver import BaseDriver
from PIL import Image
from io import BytesIO
from datetime import datetime


class SeleniumDriver(BaseDriver):
    driver: WebDriver

    def __init__(
        self,
        url: Optional[str] = None,
        get_selenium_driver: Optional[Callable[[], WebDriver]] = None,
        headless: bool = True,
        chrome_user_dir: Optional[str] = None,
    ):
        self.headless = headless
        self.chrome_user_dir = chrome_user_dir
        super().__init__(url, get_selenium_driver)

    def default_init_code(self) -> Any:
        # these imports are necessary as they will be pasted to the output
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        if self.chrome_user_dir:
            chrome_options.add_argument(f"--user-data-dir={self.chrome_user_dir}")
        chrome_options.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.resize_driver(1024, 1024)
        return self.driver

    def get_driver(self) -> WebDriver:
        return self.driver

    def resize_driver(self, width, height) -> None:
        # Selenium is only being able to set window size and not viewport size
        self.driver.set_window_size(width, height)
        viewport_height = self.driver.execute_script("return window.innerHeight;")

        height_difference = height - viewport_height
        self.driver.set_window_size(width, height + height_difference)

    def get_url(self) -> Optional[str]:
        if self.driver.current_url == "data:,":
            return None
        return self.driver.current_url

    def go_to_url_code(self, url: str) -> str:
        return f'driver.get("{url}")'

    def goto(self, url: str) -> None:
        self.driver.get(url)

    def get_html(self) -> str:
        return self.driver.page_source

    def compute_hash(self, screenshot: bytes) -> str:
        """Computes hash of a file."""
        hasher = hashlib.md5()
        hasher.update(screenshot)
        return hasher.hexdigest()

    def save_screenshot(self, current_screenshot_folder: Path) -> str:
        """Save the screenshot data to a file and return the path. If the screenshot already exists, return the path. If not save it to the folder."""
        
        new_screenshot = self.get_screenshot_as_png()
        new_hash = self.compute_hash(new_screenshot)
        new_screenshot_name = f"{new_hash}.png"
        new_screenshot_full_path = current_screenshot_folder / new_screenshot_name

        # If the screenshot does not exist, save it
        if not new_screenshot_full_path.exists():
            with open(new_screenshot_full_path, 'wb') as f:
                f.write(new_screenshot)
        return str(new_screenshot_full_path)

    def get_obs(self) -> dict:

        current_screenshot_folder = self.get_current_screenshot_folder()
        # We take a screenshot and computes its hash to see if it already exists
        self.save_screenshot(current_screenshot_folder)

        url = self.get_url()
        html = self.get_html()
        obs = {
            "html": html,
            "screenshots_path": str(current_screenshot_folder),
            "url": url,
            "date": datetime.now().isoformat()
        }
        
        return obs

    def is_bottom_of_page(self) -> bool:
        return self.driver.execute_script(
            "return (window.innerHeight + window.scrollY) >= document.body.scrollHeight;")

    def get_current_screenshot_folder(self) -> Path:
        url = self.get_url()
        screenshots_path = Path("./screenshots")
        screenshots_path.mkdir(exist_ok=True)

        current_screenshot_folder = screenshots_path / url.replace("://", "_").replace("/", "_")
        current_screenshot_folder.mkdir(exist_ok=True)
        return current_screenshot_folder
    
    def get_screenshots_whole_page(self) -> list[str]:
        screenshot_paths = []
        
        current_screenshot_folder = self.get_current_screenshot_folder()

        while True:
            # Saves a screenshot
            screenshot_path = self.save_screenshot(current_screenshot_folder)
            screenshot_paths.append(screenshot_path)
            self.driver.execute_script("window.scrollBy(0, (window.innerHeight / 1.5));")
            time.sleep(0.5)
            
            if self.is_bottom_of_page():
                break
        return screenshot_paths
        
    def get_screenshot_as_png(self) -> bytes:
        return self.driver.get_screenshot_as_png()

    def get_dummy_code(self) -> str:
        return 'driver.execute_script("window.scrollBy(0, 500)")'

    def destroy(self) -> None:
        self.driver.quit()

    def check_visibility(self, xpath: str) -> bool:
        try:
            return self.driver.find_element(By.XPATH, xpath).is_displayed()
        except:
            return False

    def exec_code(self, code: str):
        exec(self.import_lines)
        driver = self.driver
        exec(code)

    def resize_driver(self, width, targeted_height):
        """Resize the Selenium driver viewport to a targeted height and width.
        This is due to Selenium only being able to set window size and not viewport size.
        """
        self.driver.set_window_size(width, targeted_height)

        viewport_height = self.driver.execute_script("return window.innerHeight;")

        height_difference = targeted_height - viewport_height
        self.driver.set_window_size(width, targeted_height + height_difference)

    def get_capability(self) -> str:
        return SELENIUM_PROMPT_TEMPLATE
    
SELENIUM_PROMPT_TEMPLATE = '''
You are a Selenium expert in writing code to interact with web pages. You have been given a series of HTML snippets and queries.
Your goal is to write Selenium code to answer queries. Your answer must be a Python markdown only.
Always target elements by XPATH.

Provide high level explanations about why you think this element is the right one.
Your answer must be short and concise. 

Here are examples of previous answers:

HTML:
<div class="QS5gu ud1jmf" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[1]/div/div/button/div">Inloggen</div></button></div></div></div><div class="GZ7xNe" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]"><h1 class="I90TVb" id="S3BnEe" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/h1">Voordat je verdergaat naar Google</h1><div class="AG96lb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div"><div class="eLZYyf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]">We gebruiken <a class="F4a1l" href="https://policies.google.com/technologies/cookies?utm_source=ucbs&amp;hl=nl" target="_blank" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/a">cookies</a> en gegevens voor het volgende:<ul class="dbXO9" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul"><li class="gowsYd ibCF0c" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul/li[1]">Google-services leveren en onderhouden</li><li class="gowsYd GwwhGf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul/li[2]">Uitval bijhouden en bescherming bieden tegen spam, fraude en misbruik</li><li class="gowsYd v8Bpfb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul/li[3]">Doelgroepbetrokkenheid en sitestatistieken meten om inzicht te krijgen in hoe onze services worden gebruikt en de kwaliteit van die services te verbeteren</li></ul></div><div class="eLZYyf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]">Als je Alles accepteren kiest, gebruiken we cookies en gegevens ook voor het volgende:<ul class="dbXO9" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul"><li class="gowsYd M6j9qf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[1]">Nieuwe services ontwikkelen en verbeteren</li><li class="gowsYd v8Bpfb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[2]">Advertenties laten zien en de effectiviteit ervan meten</li><li class="gowsYd e21Mac" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[3]">Gepersonaliseerde content laten zien (afhankelijk van je instellingen)</li><li class="gowsYd ohEWPc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[4]">Gepersonaliseerde advertenties laten zien (afhankelijk van je instellingen)</li></ul><div class="jLhwdc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/div">Als je Alles afwijzen kiest, gebruiken we cookies niet voor deze aanvullende doeleinden.</div></div><div class="yS1nld" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[3]">Niet-gepersonaliseerde content wordt beïnvloed door factoren zoals de content die je op dat moment bekijkt, activiteit in je actieve zoeksessie en je locatie. Niet-gepersonaliseerde advertenties worden beïnvloed door de content die je op dat moment bekijkt en je algemene locatie. Gepersonaliseerde content en advertenties kunnen ook relevantere resultaten, aanbevelingen en op jou toegespitste advertenties omvatten die zijn gebaseerd op eerdere activiteit van deze browser, zoals uitgevoerde Google-zoekopdrachten. We gebruiken cookies en gegevens ook om te zorgen dat de functionaliteit geschikt is voor je leeftijd, als dit relevant is.</div><div class="yS1nld" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[4]">Selecteer Meer opties om meer informatie te bekijken, waaronder over hoe je je privacyinstellingen beheert. Je kunt ook altijd naar <span xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[4]/span">g.co/privacytools</span> gaan.</div></div></div><div class="spoKVd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]">
<div class="spoKVd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]"><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Q4cIICHw" id="W0wltc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]/div">Alles afwijzen</div></button><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiZAHCH0" id="L2AGLb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]/div">Alles accepteren</div></button></div><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiJAHCH4" id="VnjCcb" role="link" tabindex="-1" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button"><a class="eOjPIe" tabindex="0" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button/a">Meer opties</a></button></div></div><div class="XWlrff cG0Dmf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]"><a class="peRL2e" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Qj5AHCH8" href="https://policies.google.com/privacy?hl=nl&amp;fg=1&amp;utm_source=ucbs" id="RP3V5c" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]/a[1]">Privacy</a>
<div class="spoKVd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]"><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Q4cIICHw" id="W0wltc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]/div">Alles afwijzen</div></button><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiZAHCH0" id="L2AGLb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]/div">Alles accepteren</div></button></div><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiJAHCH4" id="VnjCcb" role="link" tabindex="-1" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button"><a class="eOjPIe" tabindex="0" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button/a">Meer opties</a></button></div></div><div class="XWlrff cG0Dmf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]"><a class="peRL2e" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Qj5AHCH8" href="https://policies.google.com/privacy?hl=nl&amp;fg=1&amp;utm_source=ucbs" id="RP3V5c" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]/a[1]">Privacy</a>
Query: Click on the button labeled 'Alles accepteren' to accept all cookies.
Completion:
```python
# Let's think step by step

# First, we notice that the query asks us to click on the button labeled 'Alles accepteren' to accept all cookies.

# In the provided HTML, we can see several button elements.

# We need to identify the correct button labeled 'Alles accepteren'.

# Upon examining the HTML structure, we see that the button with the text 'Alles accepteren' is located within a specific hierarchy.

# We need to navigate through the hierarchy to accurately locate this button.

# The correct button is located within a div element with a specific class and role attribute, which helps us ensure that we are targeting the right element.

# Specifically, for 'Alles accepteren', there is a button element with a unique ID 'L2AGLb' which contains a div with the text 'Alles accepteren'.

# We observe that this button element has the following XPath:
# /html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]

# Thus, we believe this is the correct element to be interacted with:
accept_all_button = driver.find_element(By.XPATH, "/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]")

# Then we can click on the button
accept_all_button.click()
```
---
HTML:
<div class="devsite-top-logo-row-middle" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]">
<div class="devsite-header-upper-tabs" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]">
<devsite-tabs class="upper-tabs devsite-overflow-menu--open" connected="" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs">
<nav aria-label="Upper tabs" class="devsite-tabs-wrapper" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav">
<tab class="devsite-active" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[1]">
<a aria-label="Gemini API, selected" class="devsite-tabs-content gc-analytics-event" data-category="Site-Wide Custom Events" data-label="Tab: Gemini API" href="https://ai.google.dev/gemini-api" track-metadata-eventdetail="https://ai.google.dev/gemini-api" track-metadata-module="primary nav" track-metadata-position="nav - gemini api" track-name="gemini api" track-type="nav" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[1]/a">
    Gemini API
  
    </a>
</tab>
<tab class="devsite-overflow-tab" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]"><!-- -->
<a aria-label="Extended Navigation" class="devsite-icon devsite-icon-arrow-drop-down" href="#" style="border: 2px solid red;" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/a"><!--?lit$8296333005$-->More</a>
<div class="devsite-tabs-overflow-menu" scrollbars="" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div">
<tab xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]">
<a class="devsite-tabs-content gc-analytics-event" data-category="Site-Wide Custom Events" data-label="Tab: Gemma" href="https://ai.google.dev/gemma" track-metadata-eventdetail="https://ai.google.dev/gemma" track-metadata-module="primary nav" track-metadata-position="nav - gemma" track-name="gemma" track-type="nav" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]/a">
    Gemma
  
    </a>
</tab><tab xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[2]">
<a class="devsite-tabs-content gc-analytics-event" data-category="Site-Wide Custom Events" data-label="Tab: Google AI Edge" href="https://ai.google.dev/edge" track-metadata-eventdetail="https://ai.google.dev/edge" track-metadata-module="primary nav" track-metadata-position="nav - google ai edge" track-name="google ai edge" track-type="nav" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[2]/a">
    Google AI Edge
  

Query: Click on "Gemma" under the "More" dropdown menu.
Completion:
```python
# Let's think step by step

# First, we notice that the query asks us to click on the "Gemma" option under the "More" dropdown menu.

# In the provided HTML, we see that the "More" dropdown menu is within a tab element with a specific class and role attribute.

# The "More" dropdown menu can be identified by its class 'devsite-overflow-tab' and contains a link element with the text 'More'.

# We need to interact with this dropdown menu to reveal the hidden options.

# Specifically, for the "More" dropdown menu, there is an anchor element within a tab element:
# /html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/a

# We can use this XPATH to identify and click on the "More" dropdown menu:
more_dropdown = driver.find_element(By.XPATH, "/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/a")
more_dropdown.click()

# After clicking the "More" dropdown, we need to select the "Gemma" option from the revealed menu.

# The "Gemma" option is located within the dropdown menu and can be identified by its anchor element with the corresponding text:
# /html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]/a

# Thus, we use this XPATH to identify and click on the "Gemma" option:
gemma_option = driver.find_element(By.XPATH, "/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]/a")
gemma_option.click()
```
---
HTML:
<div class="_8dhNBCZ2S74-" data-test="icCalendar-wrapper" style="border: 2px solid red;" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[1]/div"><span aria-hidden="true" class="irNswZTgdxU- ywR-N4gLSdc-" data-test="icCalendar" data-testid="icCalendar" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[1]/div/span"><svg viewbox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[1]/div/span/svg"><path d="M7 4a1 1 0 0 1 2 0v1h6V4a1 1 0 1 1 2 0v1h2a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2V4ZM5 7v2h14V7H5Zm0 4v8h14v-8H5Z" fill="#2D333F" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[1]/div/span/svg/path"></path></svg></span><p class="Z5-QmB-1pug-" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[1]/div/p">Tue, May 21</p></div></li><li class="c2SNlvnt0Z4-" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[2]"><div class="_8dhNBCZ2S74-" data-test="icClock-wrapper" style="border: 2px solid red;" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[2]/div"><span aria-hidden="true" class="irNswZTgdxU- ywR-N4gLSdc-" data-test="icClock" data-testid="icClock" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[2]/div/span"><svg viewbox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[2]/div/span/svg"><path d="M11 7.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5V11h1.5a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-5Z" fill="#2D333F" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[2]/div/span/svg/path[1]"></path><path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-2 0a7 7 0 1 0-14 0 7 7 0 0 0 14 0Z" fill="#2D333F" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[2]/div/span/svg/path[2]"></path></svg></span><p class="Z5-QmB-1pug-" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[2]/div/p">8:30 PM</p></div></li><li class="c2SNlvnt0Z4-" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[3]"><div class="_8dhNBCZ2S74-" data-test="icPerson-wrapper" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[3]/div"><span aria-hidden="true" class="irNswZTgdxU- ywR-N4gLSdc-" data-test="icPerson" data-testid="icPerson" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[3]/div/span"><svg viewbox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[3]/div/span/svg"><path d="M7.002 8a5 5 0 1 1 7.572 4.288c2.43.594 4.162 2.108 5.192 4.543A3 3 0 0 1 17.004 21H7a3 3 0 0 1-2.763-4.169c1.03-2.435 2.759-3.949 5.19-4.543A4.995 4.995 0 0 1 7.002 8Zm2 0A2.999 2.999 0 1 0 15 8a3 3 0 1 0-6 0Zm-2.31 10.949a.994.994 0 0 0 .316.051h9.987a1 1 0 0 0 .95-1.314C17.13 15.229 15.15 14 12.002 14c-3.15 0-5.13 1.229-5.943 3.686a.999.999 0 0 0 .634 1.263Z" fill="#2D333F" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[3]/div/span/svg/path"></path></svg></span><p class="Z5-QmB-1pug-" xpath="/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[3]/div/p">2 people</p></div></li></ul></div></div></div>
<div id="onetrust-consent-sdk" xpath="/html/body/div[2]"><div class="onetrust-pc-dark-filter ot-hide ot-fade-in" xpath="/html/body/div[2]/div[1]"></div><div aria-label="Preference center" class="otPcCenter ot-hide ot-fade-in" id="onetrust-pc-sdk" lang="en" role="region" xpath="/html/body/div[2]/div[2]"><div aria-describedby="ot-pc-desc" aria-label="Privacy Preference Center" aria-modal="true" role="alertdialog" style="height: 100%;" xpath="/html/body/div[2]/div[2]/div"><!-- Close Button --><div class="ot-pc-header" xpath="/html/body/div[2]/div[2]/div/div[1]"><!-- Logo Tag --><div aria-label="Company Logo" class="ot-pc-logo" role="img" xpath="/html/body/div[2]/div[2]/div/div[1]/div"><img alt="Company Logo" src="https://cdn.cookielaw.org/logos/static/ot_company_logo.png" xpath="/html/body/div[2]/div[2]/div/div[1]/div/img"/></div><button aria-label="Close" class="ot-close-icon" id="close-pc-btn-handler" style='background-image: url("https://cdn.cookielaw.org/logos/static/ot_close.svg");' xpath="/html/body/div[2]/div[2]/div/div[1]/button"></button></div><!-- Close Button --><div class="ot-pc-scrollbar" id="ot-pc-content" xpath="/html/body/div[2]/div[2]/div/div[2]"><div class="ot-optout-signal ot-hide" xpath="/html/body/div[2]/div[2]/div/div[2]/div[1]"><div class="ot-optout-icon" xpath="/html/body/div[2]/div[2]/div/div[2]/div[1]/div"><svg xmlns="http://www.w3.org/2000/svg" xpath="/html/body/div[2]/div[2]/div/div[2]/div[1]/div/svg"><path class="ot-floating-button__svg-fill" d="M14.588 0l.445.328c1.807 1.303 3.961 2.533 6.461 3.688 2.015.93 4.576 1.746 7.682 2.446 0 14.178-4.73 24.133-14.19 29.864l-.398.236C4.863 30.87 0 20.837 0 6.462c3.107-.7 5.668-1.516 7.682-2.446 2.709-1.251 5.01-2.59 6.906-4.016zm5.87 13.88a.75.75 0 00-.974.159l-5.475 6.625-3.005-2.997-.077-.067a.75.75 0 00-.983 1.13l4.172 4.16 6.525-7.895.06-.083a.75.75 0 00-.16-.973z" fill="#FFF" fill-rule="evenodd" xpath="/html/body/div[2]/div[2]/div/div[2]/div[1]/div/svg/path"></path></svg></div><span xpath="/html/body/div[2]/div[2]/div/div[2]/div[1]/span"></span></div><h2 id="ot-pc-title" xpath="/html/body/div[2]/div[2]/div/div[2]/h2">Privacy Preference Center</h2><div id="ot-pc-desc" xpath="/html/body/div[2]/div[2]/div/div[2]/div[2]">When you visit any website, it may store or retrieve information on your browser, mostly in the form of cookies. This information might be about you, your preferences or your device and is mostly used to make the site work as you expect it to. The information does not usually directly identify you, but it can give you a more personalized web experience. Because we respect your right to privacy, you can choose not to allow some types of cookies. Click on the different category headings to find out more and change our default settings. However, blocking some types of cookies may impact your experience of the site and the services we are able to offer.
For additional information, please visit our <a href="https://www.opentable.com/legal/cookie-policy" xpath="/html/body/div[2]/div[2]/div/div[2]/div[2]/a[1]">Cookies Policy</a> and our <a href="https://www.opentable.com/legal/privacy-policy" xpath="/html/body/div[2]/div[2]/div/div[2]/div[2]/a[2]">Privacy Policy</a>.</div><button id="accept-recommended-btn-handler" xpath="/html/body/div[2]/div[2]/div/div[2]/button">Allow All</button><section class="ot-sdk-row ot-cat-grp" xpath="/html/body/div[2]/div[2]/div/div[2]/section"><h3 id="ot-category-title" xpath="/html/body/div[2]/div[2]/div/div[2]/section/h3"> Manage Consent Preferences</h3><div class="ot-accordion-layout ot-cat-item ot-vs-config" data-optanongroupid="C0001" xpath="/html/body/div[2]/div[2]/div/div[2]/section/div[1]"><button aria-controls="ot-desc-id-C0001" aria-expanded="false" aria-labelledby="ot-header-id-C0001 ot-status-id-C0001" ot-accordion="true" xpath="/html/body/div[2]/div[2]/div/div[2]/section/div[1]/button"></button><!-- Accordion header -->
Query: Click on the date selector and choose May 25th. Then, click on the time selector and choose 1:00 PM.
Completion:
```python
# Let's think step by step

# The query asks us to first click on the date selector and choose May 25th. 
# Then, we need to click on the time selector and choose 1:00 PM.

# In the provided HTML, we can see the date selector and time selector elements within a list structure.

# We need to identify the correct elements for both the date and time selectors.

# First, we locate the date selector. It is inside a div element with a specific class and data-test attributes.
# The date selector is found at the following XPath:
date_selector = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[1]/div")

# Click on the date selector to open the date selection dropdown
date_selector.click()

# To choose May 25th, we would typically need to select it from the opened date picker. This part is omitted in the explanation for brevity.

# Next, we locate the time selector. It is also inside a div element with specific class and data-test attributes.
# The time selector is found at the following XPath:
time_selector = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/main/div/div/div/section/div[1]/div[2]/div/ul/li[2]/div")

# Click on the time selector to open the time selection dropdown
time_selector.click()
```python
'''

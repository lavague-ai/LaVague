from io import BytesIO
import json
import os
from PIL import Image
from typing import Callable, Optional, Any, Mapping
from lavague.core.utilities.format_utils import (
    extract_code_from_funct,
    keep_assignments,
    return_assigned_variables,
)
from playwright.sync_api import Page, Locator
from lavague.core.base_driver import BaseDriver


class PlaywrightDriver(BaseDriver):
    page: Page

    def __init__(
        self,
        url: Optional[str] = None,
        get_sync_playwright_page: Optional[Callable[[], Page]] = None,
        headless: bool = True,
        width: int = 1080,
        height: int = 1080,
        user_data_dir: Optional[str] = None,
    ):
        os.environ[
            "PW_TEST_SCREENSHOT_NO_FONTS_READY"
        ] = "1"  # Allow playwright to take a screenshots even if the fonts won't load in head mode.
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.width = 1080
        self.height = 1080
        super().__init__(url, get_sync_playwright_page)

    # Before modifying this function, check if your changes are compatible with code_for_init which parses this code
    # these imports are necessary as they will be pasted to the output
    def default_init_code(self) -> Page:
        try:
            from playwright.sync_api import sync_playwright
        except (ImportError, ModuleNotFoundError) as error:
            raise ImportError(
                "Please install playwright using `pip install playwright` and then `playwright install chromium` to install the necessary browser drivers"
            ) from error
        p = sync_playwright().__enter__()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
        if self.user_data_dir is None:
            browser = p.chromium.launch(headless=self.headless, user_agent=user_agent)
        else:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                user_agent=user_agent,
            )
        page = browser.new_page()
        self.page = page
        self.resize_driver(self.width, self.height)
        return self.page

    def code_for_init(self) -> str:
        init_lines = extract_code_from_funct(self.init_function)
        code_lines = [
            "from playwright.sync_api import sync_playwright",
            "",
        ]
        ignore_next = 0
        keep_else = False
        start = False
        for line in init_lines:
            if "__enter__()" in line:
                start = True
            elif not start:
                continue
            if "self.headless" in line:
                line = line.replace("self.headless", str(self.headless))
            if "self.user_data_dir" in line:
                line = line.replace("self.user_data_dir", f'"{self.user_data_dir}"')
            if "if" in line:
                if self.user_data_dir is not None:
                    ignore_next = 1
                    keep_else = True
            elif "else" in line:
                if not keep_else:
                    ignore_next = 3
            elif ignore_next <= 0:
                if "self" not in line:
                    code_lines.append(line.strip())
            else:
                ignore_next -= 1
        code_lines.append(self.code_for_resize(self.width, self.height))
        return "\n".join(code_lines) + "\n"

    def get_driver(self) -> Page:
        return self.page

    def get_screenshot_as_png(self) -> bytes:
        return self.page.screenshot(animations="disabled")

    def resize_driver(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.page.set_viewport_size({"width": width, "height": height})

    def code_for_resize(self, width, height) -> str:
        return f'page.set_viewport_size({{"width": {width}, "height": {height}}})'

    def get_url(self) -> Optional[str]:
        if self.page.url == "about:blank":
            return None
        return self.page.url

    def code_for_get(self, url: str) -> str:
        return f'page.goto("{url}")'

    def get(self, url: str) -> None:
        return self.page.goto(url)

    def back(self) -> None:
        return self.page.go_back()

    def code_for_back(self) -> None:
        return "page.go_back()"

    def get_html(self) -> str:
        return self.page.content()

    def destroy(self) -> None:
        self.page.close()

    def check_visibility(self, xpath: str) -> bool:
        try:
            locator = self.page.locator(f"xpath={xpath}")
            return locator.is_visible() and locator.is_enabled()
        except:
            return False

    def get_highlighted_element(self, generated_code: str):
        elements = []

        data = json.loads(generated_code)
        for item in data:
            action_name = item["action"]["name"]
            if action_name != "fail":
                xpath = item["action"]["args"]["xpath"]
                elem = self.page.locator(f"xpath={xpath}").first
                elements.append(elem)

        if len(elements) == 0:
            raise ValueError(f"No element found.")

        outputs = []
        for element in elements:
            element: Locator

            bounding_box = {}
            viewport_size = {}

            self.execute_script(
                "arguments[0].setAttribute('style', arguments[1]);",
                element,
                "border: 2px solid red;",
            )
            self.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", element
            )
            screenshot = self.get_screenshot_as_png()

            bounding_box["x1"] = element.bounding_box()["x"]
            bounding_box["y1"] = element.bounding_box()["y"]
            bounding_box["x2"] = bounding_box["x1"] + element.bounding_box()["width"]
            bounding_box["y2"] = bounding_box["y1"] + element.bounding_box()["height"]

            viewport_size["width"] = self.execute_script("return window.innerWidth;")
            viewport_size["height"] = self.execute_script("return window.innerHeight;")
            screenshot = BytesIO(screenshot)
            screenshot = Image.open(screenshot)
            output = {
                "screenshot": screenshot,
                "bounding_box": bounding_box,
                "viewport_size": viewport_size,
            }
            outputs.append(output)
        return outputs

    def maximize_window(self) -> None:
        pass

    def exec_code(
        self,
        code: str,
        globals: dict[str, Any] = None,
        locals: Mapping[str, object] = None,
    ):
        data = json.loads(code)
        for item in data:
            action_name = item["action"]["name"]
            if action_name == "click":
                self.click(item["action"]["args"]["xpath"])
            elif action_name == "setValue":
                self.set_value(
                    item["action"]["args"]["xpath"], item["action"]["args"]["value"]
                )
            elif action_name == "setValueAndEnter":
                self.set_value(
                    item["action"]["args"]["xpath"],
                    item["action"]["args"]["value"],
                    True,
                )

    def execute_script(self, js_code: str, *args) -> Any:
        args = list(arg for arg in args)
        for i, arg in enumerate(args):
            if type(arg) == Locator:
                args[i] = arg.element_handle()  # playwright only accept element_handles
        script = f"(arguments) => {{{js_code}}}"
        return self.page.evaluate(script, args)

    def click(self, xpath: str):
        elem = self.page.locator(f"xpath={xpath}").first
        elem.click()

    def set_value(self, xpath: str, value: str, enter: bool = False):
        elem = self.page.locator(f"xpath={xpath}").first
        elem.click()
        elem.fill(value)
        if enter:
            elem.press("Enter")

    def code_for_execute_script(self, js_code: str, *args) -> str:
        return f"page.evaluate(\"(arguments) => {{{js_code}}}\", [{', '.join(str(arg) for arg in args)}])"

    def scroll_up(self):
        code = self.execute_script("window.scrollBy(0, -window.innerHeight);")

    def scroll_down(self):
        code = self.execute_script("window.scrollBy(0, window.innerHeight);")

    def get_capability(self) -> str:
        return """
You are a chrome extension and your goal is to interact with web pages. You have been given a series of HTML snippets and queries.
Your goal is to return a list of actions that should be done in order to execute the actions.
Always target elements by XPATH.

The actions available are:

Name: click
Description: Click on an element with a specific xpath
Arguments:
  - xpath (string)

Name: setValue
Description: Focus on and set the value of an input element with a specific xpath
Arguments:
  - xpath (string)
  - value (string)

Name: setValueAndEnter
Description: Like "setValue", except then it presses ENTER. Use this tool can submit the form when there's no "submit" button.
Arguments:
  - xpath (string)
  - value (string)

Name: fail
Description: Indicate that you are unable to complete the task
No arguments.

Here are examples of previous answers:
HTML:
<div class="QS5gu ud1jmf" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[1]/div/div/button/div">Inloggen</div></button></div></div></div><div class="GZ7xNe" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]"><h1 class="I90TVb" id="S3BnEe" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/h1">Voordat je verdergaat naar Google</h1><div class="AG96lb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div"><div class="eLZYyf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]">We gebruiken <a class="F4a1l" href="https://policies.google.com/technologies/cookies?utm_source=ucbs&amp;hl=nl" target="_blank" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/a">cookies</a> en gegevens voor het volgende:<ul class="dbXO9" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul"><li class="gowsYd ibCF0c" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul/li[1]">Google-services leveren en onderhouden</li><li class="gowsYd GwwhGf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul/li[2]">Uitval bijhouden en bescherming bieden tegen spam, fraude en misbruik</li><li class="gowsYd v8Bpfb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul/li[3]">Doelgroepbetrokkenheid en sitestatistieken meten om inzicht te krijgen in hoe onze services worden gebruikt en de kwaliteit van die services te verbeteren</li></ul></div><div class="eLZYyf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]">Als je Alles accepteren kiest, gebruiken we cookies en gegevens ook voor het volgende:<ul class="dbXO9" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul"><li class="gowsYd M6j9qf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[1]">Nieuwe services ontwikkelen en verbeteren</li><li class="gowsYd v8Bpfb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[2]">Advertenties laten zien en de effectiviteit ervan meten</li><li class="gowsYd e21Mac" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[3]">Gepersonaliseerde content laten zien (afhankelijk van je instellingen)</li><li class="gowsYd ohEWPc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[4]">Gepersonaliseerde advertenties laten zien (afhankelijk van je instellingen)</li></ul><div class="jLhwdc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/div">Als je Alles afwijzen kiest, gebruiken we cookies niet voor deze aanvullende doeleinden.</div></div><div class="yS1nld" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[3]">Niet-gepersonaliseerde content wordt beïnvloed door factoren zoals de content die je op dat moment bekijkt, activiteit in je actieve zoeksessie en je locatie. Niet-gepersonaliseerde advertenties worden beïnvloed door de content die je op dat moment bekijkt en je algemene locatie. Gepersonaliseerde content en advertenties kunnen ook relevantere resultaten, aanbevelingen en op jou toegespitste advertenties omvatten die zijn gebaseerd op eerdere activiteit van deze browser, zoals uitgevoerde Google-zoekopdrachten. We gebruiken cookies en gegevens ook om te zorgen dat de functionaliteit geschikt is voor je leeftijd, als dit relevant is.</div><div class="yS1nld" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[4]">Selecteer Meer opties om meer informatie te bekijken, waaronder over hoe je je privacyinstellingen beheert. Je kunt ook altijd naar <span xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[4]/span">g.co/privacytools</span> gaan.</div></div></div><div class="spoKVd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]">
<div class="spoKVd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]"><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Q4cIICHw" id="W0wltc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]/div">Alles afwijzen</div></button><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiZAHCH0" id="L2AGLb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]/div">Alles accepteren</div></button></div><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiJAHCH4" id="VnjCcb" role="link" tabindex="-1" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button"><a class="eOjPIe" tabindex="0" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button/a">Meer opties</a></button></div></div><div class="XWlrff cG0Dmf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]"><a class="peRL2e" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Qj5AHCH8" href="https://policies.google.com/privacy?hl=nl&amp;fg=1&amp;utm_source=ucbs" id="RP3V5c" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]/a[1]">Privacy</a>
<div class="spoKVd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]"><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Q4cIICHw" id="W0wltc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]/div">Alles afwijzen</div></button><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiZAHCH0" id="L2AGLb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]/div">Alles accepteren</div></button></div><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiJAHCH4" id="VnjCcb" role="link" tabindex="-1" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button"><a class="eOjPIe" tabindex="0" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button/a">Meer opties</a></button></div></div><div class="XWlrff cG0Dmf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]"><a class="peRL2e" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Qj5AHCH8" href="https://policies.google.com/privacy?hl=nl&amp;fg=1&amp;utm_source=ucbs" id="RP3V5c" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]/a[1]">Privacy</a>
Query: Click on the button labeled 'Alles accepteren' to accept all cookies.
Completion:
[
    {
        "action": {
            "name": "click",
            "args": {
            "xpath": "/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]"
            }
        }
    }
]
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
[
    {
        "action": {
            "name": "click",
            "args": {
            "xpath": "/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/a"
            }
        }
    },
    {
        "action": {
            "name": "click",
            "args": {
            "xpath": "/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]/a"
            }
        }
    }
]
Your response must always be in JSON format and must include object "action", which contains the string "name" of tool of choice, and necessary arguments ("args") if required by the tool.
"""

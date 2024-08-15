from typing import Any, Optional, Callable, Mapping, Dict, List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from lavague.core.base_driver import (
    BaseDriver,
    JS_GET_INTERACTIVES,
    JS_GET_INTERACTIVES_IN_VIEWPORT,
    JS_WAIT_DOM_IDLE,
    JS_GET_SCROLLABLE_PARENT,
    PossibleInteractionsByXpath,
    ScrollDirection,
    InteractionType,
    DOMNode,
)
from lavague.core.exceptions import (
    CannotBackException,
    NoElementException,
    AmbiguousException,
)
from PIL import Image
from io import BytesIO
from selenium.webdriver.chrome.options import Options
from lavague.core.utilities.format_utils import (
    extract_code_from_funct,
    quote_numeric_yaml_values,
)
from selenium.webdriver.common.action_chains import ActionChains
import time
import yaml
import json
from selenium.webdriver.remote.remote_connection import RemoteConnection
import requests
import os


class SeleniumDriver(BaseDriver):
    driver: WebDriver
    last_hover_xpath: Optional[str] = None

    def __init__(
        self,
        url: Optional[str] = None,
        get_selenium_driver: Optional[Callable[[], WebDriver]] = None,
        headless: bool = True,
        user_data_dir: Optional[str] = None,
        width: int = 1080,
        height: int = 1080,
        options: Optional[Options] = None,
        driver: Optional[WebDriver] = None,
        log_waiting_time=False,
        waiting_completion_timeout=10,
        remote_connection: "BrowserbaseRemoteConnection" = None,
    ):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.width = width
        self.height = height
        self.options = options
        self.driver = driver
        self.log_waiting_time = log_waiting_time
        self.waiting_completion_timeout = waiting_completion_timeout
        self.remote_connection = remote_connection
        super().__init__(url, get_selenium_driver)

    #   Default code to init the driver.
    #   Before making any change to this, make sure it is compatible with code_for_init, which parses the code of this function
    #   These imports are necessary as they will be pasted to the output
    def default_init_code(self) -> Any:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        from lavague.core.base_driver import JS_SETUP_GET_EVENTS

        if self.options:
            chrome_options = self.options
        else:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless=new")
            if self.user_data_dir:
                chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
            user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
            chrome_options.add_argument(f"user-agent={user_agent}")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.page_load_strategy = "normal"
        # allow access to cross origin iframes
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-site-isolation-trials")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        if self.remote_connection:
            chrome_options.add_experimental_option("debuggerAddress", "localhost:9223")
            self.driver = webdriver.Remote(
                self.remote_connection, options=chrome_options
            )
        elif self.driver is None:
            self.driver = webdriver.Chrome(options=chrome_options)

            # 538: browserbase implementation - move execute_cdp_cmd to inner block to avoid error
            # AttributeError: 'WebDriver' object has no attribute 'execute_cdp_cmd'
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": JS_SETUP_GET_EVENTS},
            )
        self.resize_driver(self.width, self.height)
        return self.driver

    def code_for_init(self) -> str:
        init_lines = extract_code_from_funct(self.init_function)
        code_lines = []
        keep_next = True
        for line in init_lines:
            if "--user-data-dir" in line:
                line = line.replace(
                    f"{{self.user_data_dir}}", f'"{self.user_data_dir}"'
                )
            if "if" in line:
                if ("headless" in line and not self.headless) or (
                    "user_data_dir" in line and self.user_data_dir is None
                ):
                    keep_next = False
            elif keep_next:
                if "self" not in line:
                    code_lines.append(line.strip())
            else:
                keep_next = True
        code_lines.append(self.code_for_resize(self.width, self.height))
        return "\n".join(code_lines) + "\n"

    def get_driver(self) -> WebDriver:
        return self.driver

    def resize_driver(self, width, height) -> None:
        # Selenium is only being able to set window size and not viewport size
        self.driver.set_window_size(width, height)
        viewport_height = self.driver.execute_script("return window.innerHeight;")

        height_difference = height - viewport_height
        self.driver.set_window_size(width, height + height_difference)
        self.width = width
        self.height = height

    def code_for_resize(self, width, height) -> str:
        return f"""
driver.set_window_size({width}, {height})
viewport_height = driver.execute_script("return window.innerHeight;")
height_difference = {height} - viewport_height
driver.set_window_size({width}, {height} + height_difference)
"""

    def get_url(self) -> Optional[str]:
        if self.driver.current_url == "data:,":
            return None
        return self.driver.current_url

    def code_for_get(self, url: str) -> str:
        return f'driver.get("{url}")'

    def get(self, url: str) -> None:
        self.driver.get(url)

    def back(self) -> None:
        if self.driver.execute_script("return !document.referrer"):
            raise CannotBackException()
        self.driver.back()

    def code_for_back(self) -> None:
        return "driver.back()"

    def get_html(self) -> str:
        return self.driver.page_source

    def get_screenshot_as_png(self) -> bytes:
        return self.driver.get_screenshot_as_png()

    def destroy(self) -> None:
        self.driver.quit()

    def maximize_window(self) -> None:
        self.driver.maximize_window()

    def check_visibility(self, xpath: str) -> bool:
        try:
            element = self.resolve_xpath(xpath)
            return (
                element is not None and element.is_displayed() and element.is_enabled()
            )
        except:
            return False

    def get_highlighted_element(self, generated_code: str):
        elements = []

        # Ensures that numeric values are quoted
        generated_code = quote_numeric_yaml_values(generated_code)

        data = yaml.safe_load(generated_code)
        if not isinstance(data, List):
            data = [data]
        for item in data:
            for action in item["actions"]:
                try:
                    xpath = action["action"]["args"]["xpath"]
                    elem = self.driver.find_element(By.XPATH, xpath)
                    elements.append(elem)
                except:
                    pass

        outputs = []
        for element in elements:
            element: WebElement

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

            bounding_box["x1"] = element.location["x"]
            bounding_box["y1"] = element.location["y"]
            bounding_box["x2"] = bounding_box["x1"] + element.size["width"]
            bounding_box["y2"] = bounding_box["y1"] + element.size["height"]

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

    def switch_frame(self, xpath):
        iframe = self.driver.find_element(By.XPATH, xpath)
        self.driver.switch_to.frame(iframe)

    def switch_default_frame(self) -> None:
        self.driver.switch_to.default_content()

    def switch_parent_frame(self) -> None:
        self.driver.switch_to.parent_frame()

    def resolve_xpath(self, xpath: Optional[str]) -> WebElement:
        if not xpath:
            raise NoSuchElementException("xpath is missing")
        before, sep, after = xpath.partition("iframe")
        if len(before) == 0:
            return None
        if len(sep) == 0:
            return self.driver.find_element(By.XPATH, before)
        self.switch_frame(before + sep)
        element = self.resolve_xpath(after)
        self.switch_default_frame()
        return element

    def exec_code(
        self,
        code: str,
        globals: dict[str, Any] = None,
        locals: Mapping[str, object] = None,
    ):
        # Ensures that numeric values are quoted to avoid issues with YAML parsing
        code = quote_numeric_yaml_values(code)

        data = yaml.safe_load(code)
        if not isinstance(data, List):
            data = [data]
        for item in data:
            for action in item["actions"]:
                action_name = action["action"]["name"]
                args = action["action"]["args"]
                xpath = args.get("xpath", None)

                match action_name:
                    case "click":
                        self.click(xpath)
                    case "setValue":
                        self.set_value(xpath, args["value"])
                    case "setValueAndEnter":
                        self.set_value(xpath, args["value"], True)
                    case "dropdownSelect":
                        self.dropdown_select(xpath, args["value"])
                    case "hover":
                        self.hover(xpath)
                    case "scroll":
                        self.scroll(
                            xpath,
                            ScrollDirection.from_string(args.get("value", "DOWN")),
                        )
                    case "failNoElement":
                        raise NoElementException("No element: " + args["value"])
                    case "failAmbiguous":
                        raise AmbiguousException("Ambiguous: " + args["value"])
                    case _:
                        raise ValueError(f"Unknown action: {action_name}")

                self.wait_for_idle()

    def execute_script(self, js_code: str, *args) -> Any:
        return self.driver.execute_script(js_code, *args)

    def scroll_up(self):
        self.scroll(direction=ScrollDirection.UP)

    def scroll_down(self):
        self.scroll(direction=ScrollDirection.DOWN)

    def code_for_execute_script(self, js_code: str, *args) -> str:
        return (
            f"driver.execute_script({js_code}, {', '.join(str(arg) for arg in args)})"
        )

    def hover(self, xpath: str):
        element = self.resolve_xpath(xpath)
        self.last_hover_xpath = xpath
        ActionChains(self.driver).move_to_element(element).perform()

    def scroll_page(self, direction: ScrollDirection = ScrollDirection.DOWN):
        self.driver.execute_script(direction.get_page_script())

    def get_scroll_anchor(self, xpath_anchor: Optional[str] = None) -> WebElement:
        element = self.resolve_xpath(xpath_anchor or self.last_hover_xpath)
        parent = self.driver.execute_script(JS_GET_SCROLLABLE_PARENT, element)
        scroll_anchor = parent or element
        return scroll_anchor

    def get_scroll_container_size(self, scroll_anchor: WebElement):
        container = self.driver.execute_script(JS_GET_SCROLLABLE_PARENT, scroll_anchor)
        if container:
            return (
                self.driver.execute_script(
                    "const r = arguments[0].getBoundingClientRect(); return [r.width, r.height]",
                    scroll_anchor,
                ),
                True,
            )
        return (
            self.driver.execute_script(
                "return [window.innerWidth, window.innerHeight]",
            ),
            False,
        )

    def is_bottom_of_page(self) -> bool:
        return not self.can_scroll(direction=ScrollDirection.DOWN)

    def can_scroll(
        self,
        xpath_anchor: Optional[str] = None,
        direction: ScrollDirection = ScrollDirection.DOWN,
    ) -> bool:
        try:
            scroll_anchor = self.get_scroll_anchor(xpath_anchor)
            return self.driver.execute_script(
                direction.get_script_element_is_scrollable(),
                scroll_anchor,
            )
        except NoSuchElementException:
            return self.driver.execute_script(direction.get_script_page_is_scrollable())

    def scroll(
        self,
        xpath_anchor: Optional[str] = None,
        direction: ScrollDirection = ScrollDirection.DOWN,
        scroll_factor=0.75,
    ):
        try:
            scroll_anchor = self.get_scroll_anchor(xpath_anchor)
            size, is_container = self.get_scroll_container_size(scroll_anchor)
            scroll_xy = direction.get_scroll_xy(size, scroll_factor)
            if is_container:
                ActionChains(self.driver).move_to_element(
                    scroll_anchor
                ).scroll_from_origin(
                    ScrollOrigin(scroll_anchor, 0, 0), scroll_xy[0], scroll_xy[1]
                ).perform()
            else:
                ActionChains(self.driver).scroll_by_amount(
                    scroll_xy[0], scroll_xy[1]
                ).perform()
            if xpath_anchor:
                self.last_hover_xpath = xpath_anchor
        except NoSuchElementException:
            self.scroll_page(direction)

    def click(self, xpath: str):
        element = self.resolve_xpath(xpath)
        self.last_hover_xpath = xpath
        try:
            element.click()
        except ElementClickInterceptedException:
            try:
                # Move to the element and click at its position
                ActionChains(self.driver).move_to_element(element).click().perform()
            except WebDriverException as click_error:
                raise Exception(
                    f"Failed to click at element coordinates of {xpath} : {str(click_error)}"
                )
        except Exception as e:
            raise Exception(
                f"An unexpected error occurred when trying to click on {xpath}: {str(e)}"
            )
        self.driver.switch_to.default_content()

    def set_value(self, xpath: str, value: str, enter: bool = False):
        try:
            elem = self.resolve_xpath(xpath)
            self.last_hover_xpath = xpath
            if elem.tag_name == "select":
                # use the dropdown_select to set the value of a select
                return self.dropdown_select(xpath, value)
            if elem.tag_name == "input" and elem.get_attribute("type") == "file":
                # set the value of a file input
                return self.upload_file(xpath, value)

            elem.clear()
        except:
            # might not be a clearable element, but global click + send keys can still success
            pass

        self.click(xpath)

        (
            ActionChains(self.driver)
            .key_down(Keys.CONTROL)
            .send_keys("a")
            .key_up(Keys.CONTROL)
            .send_keys(Keys.DELETE)  # clear the input field
            .send_keys(value)
            .perform()
        )
        if enter:
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        self.driver.switch_to.default_content()

    def dropdown_select(self, xpath: str, value: str):
        element = self.resolve_xpath(xpath)
        self.last_hover_xpath = xpath

        if element.tag_name != "select":
            print(
                f"Cannot use dropdown_select on {element.tag_name}, falling back to simple click on {xpath}"
            )
            return self.click(xpath)

        select = Select(element)
        try:
            select.select_by_value(value)
        except NoSuchElementException:
            select.select_by_visible_text(value)
        self.driver.switch_to.default_content()

    def upload_file(self, xpath: str, file_path: str):
        element = self.resolve_xpath(xpath)
        self.last_hover_xpath = xpath
        element.send_keys(file_path)

    def perform_wait(self, duration: float):
        import time

        time.sleep(duration)

    def is_idle(self):
        active = 0
        logs = self.driver.get_log("performance")
        active = 0
        request_ids = set()
        for log in logs:
            log_json = json.loads(log["message"])["message"]
            method = log_json["method"]
            if method == "Network.requestWillBeSent":
                request_ids.add(log_json["params"]["requestId"])
            elif method in ("Network.loadingFinished", "Network.loadingFailed"):
                request_ids.discard(log_json["params"]["requestId"])
            elif method in ("Page.frameStartedLoading", "Browser.downloadWillBegin"):
                active += 1
            elif method == "Page.frameStoppedLoading":
                active -= 1
            elif method == "Browser.downloadProgress" and log_json["params"][
                "state"
            ] in (
                "completed",
                "canceled",
            ):
                active -= 1

        return len(request_ids) == 0 and active <= 0

    def wait_for_dom_stable(self, timeout=10):
        self.driver.execute_script(JS_WAIT_DOM_IDLE, max(0, round(timeout * 1000)))

    def wait_for_idle(self):
        t = time.time()
        elapsed = 0
        try:
            WebDriverWait(self.driver, self.waiting_completion_timeout).until(
                lambda d: self.is_idle()
            )
            elapsed = time.time() - t
            self.wait_for_dom_stable(self.waiting_completion_timeout - elapsed)
        except TimeoutException:
            pass

        total_elapsed = time.time() - t
        if self.log_waiting_time or total_elapsed > 10:
            print(
                f"Waited {total_elapsed}s for browser being idle ({elapsed} for network + {total_elapsed - elapsed} for DOM)"
            )

    def get_capability(self) -> str:
        return SELENIUM_PROMPT_TEMPLATE

    def get_tabs(self):
        driver = self.driver
        window_handles = driver.window_handles
        # Store the current window handle (focused tab)
        current_handle = driver.current_window_handle
        tab_info = []
        tab_id = 0

        for handle in window_handles:
            # Switch to each tab
            driver.switch_to.window(handle)

            # Get the title of the current tab
            title = driver.title

            # Check if this is the focused tab
            if handle == current_handle:
                tab_info.append(f"{tab_id} - [CURRENT] {title}")
            else:
                tab_info.append(f"{tab_id} - {title}")

            tab_id += 1

        # Switch back to the original tab
        driver.switch_to.window(current_handle)

        tab_info = "\n".join(tab_info)
        tab_info = "Tabs opened:\n" + tab_info
        return tab_info

    def switch_tab(self, tab_id: int):
        driver = self.driver
        window_handles = driver.window_handles

        # Switch to the tab with the given id
        driver.switch_to.window(window_handles[tab_id])

    def get_nodes(self, xpaths: List[str]) -> List["SeleniumNode"]:
        return [SeleniumNode(xpath, self.driver) for xpath in xpaths]

    def exec_script_for_nodes(self, nodes: List["SeleniumNode"], script: str):
        standard_nodes: List[SeleniumNode] = []
        special_nodes: List[SeleniumNode] = []

        for node in nodes:
            # iframe and shadow DOM must use the resolve_xpath method
            target = (
                special_nodes
                if "iframe" in node.xpath or "//" in node.xpath
                else standard_nodes
            )
            target.append(node)

        if len(standard_nodes) > 0:
            self.driver.execute_script(
                "arguments[0]=arguments[0].map(a => document.evaluate(a, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue).filter(a => a);"
                + script,
                [n.xpath for n in standard_nodes],
            )

        if len(special_nodes) > 0:
            self.driver.execute_script(
                script,
                [n.element for n in special_nodes if n.element],
            )

    def remove_nodes_highlight(self, xpaths: List[str]):
        self.exec_script_for_nodes(
            self.get_nodes(xpaths),
            "arguments[0].filter(a => a).forEach(a => a.style.removeProperty('outline'))",
        )

    def highlight_nodes(self, xpaths: List[str], color: str = "red") -> Callable:
        nodes = self.get_nodes(xpaths)
        set_style = f"a.style.outline = '2px dashed {color}'; a.style['outline-offset'] = '-1px'"
        self.exec_script_for_nodes(
            nodes, "arguments[0].forEach(a => { " + set_style + "})"
        )
        return self._add_highlighted_destructors(
            lambda: self.remove_nodes_highlight(xpaths)
        )

    def get_possible_interactions(
        self, in_viewport=True, foreground_only=True
    ) -> PossibleInteractionsByXpath:
        exe: Dict[str, List[str]] = self.driver.execute_script(
            JS_GET_INTERACTIVES_IN_VIEWPORT if in_viewport else JS_GET_INTERACTIVES,
            foreground_only,
        )
        res = dict()
        for k, v in exe.items():
            res[k] = set(InteractionType[i] for i in v)
        return res


class SeleniumNode(DOMNode):
    def __init__(self, xpath: str, driver: SeleniumDriver) -> None:
        self.xpath = xpath
        self._driver = driver
        super().__init__()

    @property
    def element(self):
        if hasattr(self, "_element"):
            return self._element
        try:
            self._element = self._driver.resolve_xpath(self.xpath)
        except StaleElementReferenceException:
            self._element = None
        return self._element

    def highlight(self, color: str = "red"):
        self._driver.highlight_nodes([self.xpath], color)
        return self

    def clear(self):
        self._driver.remove_nodes_highlight([self.xpath])
        return self

    def take_screenshot(self):
        try:
            return Image.open(BytesIO(self.element.screenshot_as_png))
        except WebDriverException:
            return Image.new("RGB", (0, 0))

    def get_html(self):
        return self._driver.driver.execute_script(
            "return arguments[0].outerHTML", self.element
        )


class BrowserbaseRemoteConnection(RemoteConnection):
    _session_id = None

    def __init__(
        self, remote_server_addr: str, api_key: str = None, project_id: str = None
    ):
        super().__init__(remote_server_addr)
        self.api_key = api_key or os.environ["BROWSERBASE_API_KEY"]
        self.project_id = project_id or os.environ["BROWSERBASE_PROJECT_ID"]

    def get_remote_connection_headers(self, parsed_url, keep_alive=False):
        if self._session_id is None:
            self._session_id = self._create_session()
        headers = super().get_remote_connection_headers(parsed_url, keep_alive)
        headers.update({"x-bb-api-key": self.api_key})
        headers.update({"session-id": self._session_id})
        return headers

    def _create_session(self):
        url = "https://www.browserbase.com/v1/sessions"
        headers = {"Content-Type": "application/json", "x-bb-api-key": self.api_key}
        response = requests.post(
            url, json={"projectId": self.project_id}, headers=headers
        )
        return response.json()["id"]


SELENIUM_PROMPT_TEMPLATE = """
You are a chrome extension and your goal is to interact with web pages. You have been given a series of HTML snippets and queries.
Your goal is to return a list of actions that should be done in order to execute the actions.
Always target elements by XPATH. You can only use one of the Xpaths included in the HTML. Do not derive new Xpaths.

Your response must always be in the YAML format with the yaml markdown indicator and must include the main item "actions" , which will contains the objects "action", which contains the string "name" of tool of choice, and necessary arguments ("args") if required by the tool. 
There must be only ONE args sub-object, such as args (if the tool has multiple arguments). 
You must always include the comments as well, describing your actions step by step, following strictly the format in the examples provided.

Provide high level explanations about why you think this element is the right one.
Your answer must be short and concise. Always includes comments in the YAML before listing the actions.

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
  
Name: dropdownSelect
Description: Select an option from a dropdown menu by its value
Arguments:
    - xpath (string)
    - value (string)

Name: setValueAndEnter
Description: Like "setValue", except then it presses ENTER. Use this tool can submit the form when there's no "submit" button.
Arguments:
  - xpath (string)
  - value (string)

Name: hover
Description: Move the mouse cursor over an element identified by the given xpath. It can be used to reveal tooltips or dropdown that appear on hover. It can also be used before scrolling to ensure the focus is in the correct container before performing the scroll action.
Arguments:
  - xpath (string)

Name: scroll
Description: Scroll the container that holds the element identified by the given xpath
Arguments:
  - xpath (string)
  - value (string): UP or DOWN

Name: failNoElement
Description: Indicate that you are unable to find an element that could match.
Arguments:
  - xpath (string): Always set to an empty string
  - value (string): Detailled explanation to clarify the non-existence of any relevant element

Name: failAmbiguous 
Description: Indicate that the provided information is too vague or unclear to successfully choose between multiple elements.
Arguments:
  - xpath (string): Always set to an empty string
  - value (string): Detailled explanation such as unclear instructions or multiple possible interpretations

Here are examples of previous answers:
HTML:
<div class="QS5gu ud1jmf" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[1]/div/div/button/div">Inloggen</div></button></div></div></div><div class="GZ7xNe" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]"><h1 class="I90TVb" id="S3BnEe" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/h1">Voordat je verdergaat naar Google</h1><div class="AG96lb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div"><div class="eLZYyf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]">We gebruiken <a class="F4a1l" href="https://policies.google.com/technologies/cookies?utm_source=ucbs&amp;hl=nl" target="_blank" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/a">cookies</a> en gegevens voor het volgende:<ul class="dbXO9" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul"><li class="gowsYd ibCF0c" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul/li[1]">Google-services leveren en onderhouden</li><li class="gowsYd GwwhGf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul/li[2]">Uitval bijhouden en bescherming bieden tegen spam, fraude en misbruik</li><li class="gowsYd v8Bpfb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[1]/ul/li[3]">Doelgroepbetrokkenheid en sitestatistieken meten om inzicht te krijgen in hoe onze services worden gebruikt en de kwaliteit van die services te verbeteren</li></ul></div><div class="eLZYyf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]">Als je Alles accepteren kiest, gebruiken we cookies en gegevens ook voor het volgende:<ul class="dbXO9" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul"><li class="gowsYd M6j9qf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[1]">Nieuwe services ontwikkelen en verbeteren</li><li class="gowsYd v8Bpfb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[2]">Advertenties laten zien en de effectiviteit ervan meten</li><li class="gowsYd e21Mac" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[3]">Gepersonaliseerde content laten zien (afhankelijk van je instellingen)</li><li class="gowsYd ohEWPc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/ul/li[4]">Gepersonaliseerde advertenties laten zien (afhankelijk van je instellingen)</li></ul><div class="jLhwdc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[2]/div">Als je Alles afwijzen kiest, gebruiken we cookies niet voor deze aanvullende doeleinden.</div></div><div class="yS1nld" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[3]">Niet-gepersonaliseerde content wordt beïnvloed door factoren zoals de content die je op dat moment bekijkt, activiteit in je actieve zoeksessie en je locatie. Niet-gepersonaliseerde advertenties worden beïnvloed door de content die je op dat moment bekijkt en je algemene locatie. Gepersonaliseerde content en advertenties kunnen ook relevantere resultaten, aanbevelingen en op jou toegespitste advertenties omvatten die zijn gebaseerd op eerdere activiteit van deze browser, zoals uitgevoerde Google-zoekopdrachten. We gebruiken cookies en gegevens ook om te zorgen dat de functionaliteit geschikt is voor je leeftijd, als dit relevant is.</div><div class="yS1nld" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[4]">Selecteer Meer opties om meer informatie te bekijken, waaronder over hoe je je privacyinstellingen beheert. Je kunt ook altijd naar <span xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[2]/div/div[4]/span">g.co/privacytools</span> gaan.</div></div></div><div class="spoKVd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]">
<div class="spoKVd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]"><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Q4cIICHw" id="W0wltc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]/div">Alles afwijzen</div></button><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiZAHCH0" id="L2AGLb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]/div">Alles accepteren</div></button></div><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiJAHCH4" id="VnjCcb" role="link" tabindex="-1" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button"><a class="eOjPIe" tabindex="0" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button/a">Meer opties</a></button></div></div><div class="XWlrff cG0Dmf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]"><a class="peRL2e" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Qj5AHCH8" href="https://policies.google.com/privacy?hl=nl&amp;fg=1&amp;utm_source=ucbs" id="RP3V5c" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]/a[1]">Privacy</a>
<div class="spoKVd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]"><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Q4cIICHw" id="W0wltc" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[1]/div">Alles afwijzen</div></button><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiZAHCH0" id="L2AGLb" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]"><div class="QS5gu sy4vM" role="none" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]/div">Alles accepteren</div></button></div><div class="GzLjMd" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]"><button class="tHlp8d" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4QiJAHCH4" id="VnjCcb" role="link" tabindex="-1" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button"><a class="eOjPIe" tabindex="0" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[2]/button/a">Meer opties</a></button></div></div><div class="XWlrff cG0Dmf" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]"><a class="peRL2e" data-ved="0ahUKEwjX3bmBmKeGAxU2xQIHHcGoAg4Qj5AHCH8" href="https://policies.google.com/privacy?hl=nl&amp;fg=1&amp;utm_source=ucbs" id="RP3V5c" xpath="/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[4]/a[1]">Privacy</a>
Query: Click on the button labeled 'Alles accepteren' to accept all cookies.
Completion:
```yaml
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

- actions:
    - action:
        # Thus, we believe this is the correct element to be interacted with:
        args:
            xpath: "/html/body/div[2]/div[2]/div[3]/span/div/div/div/div[3]/div[1]/button[2]"
            value: ""
        # Then we can click on the button
        name: "click"
```
-----
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
```yaml
# Let's think step by step
# First, we notice that the query asks us to click on the "Gemma" option under the "More" dropdown menu.
# In the provided HTML, we see that the "More" dropdown menu is within a tab element with a specific class and role attribute.
# The "More" dropdown menu can be identified by its class 'devsite-overflow-tab' and contains a link element with the text 'More'.
# We need to interact with this dropdown menu to reveal the hidden options.
# Specifically, for the "More" dropdown menu, there is an anchor element within a tab element:
# /html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/a

- actions:
    - action:
        # We can use this XPATH to identify and click on the "More" dropdown menu:
        args:
            xpath: "/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/a"
            value: ""
        name: "click"
    - action:
        # After clicking the "More" dropdown, we need to select the "Gemma" option from the revealed menu.
        # The "Gemma" option is located within the dropdown menu and can be identified by its anchor element with the corresponding text:
        # /html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]/a
        # Thus, we use this XPATH to identify and click on the "Gemma" option:
        args:
            xpath: "/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]/a"
            value: ""
        name: "click"
```
-----
HTML:
<select name="checkin_eta_hour" xpath="/html/body/div/main/form/section/div/select">
<option disabled="" selected="" value="">Please select</option>
<option value="-1">I don't know</option>
<option value="0">12:00 AM – 1:00 AM </option>
<option value="1">1:00 AM – 2:00 AM </option>
<option value="2">2:00 AM – 3:00 AM </option>
<option value="3">3:00 AM – 4:00 AM </option>
</select>

Query: Select the 2:00 AM - 3:00 AM option from the dropdown menu
Completion:
```yaml
# Let's think step by step
# The query asks us to select the "2:00 AM - 3:00 AM" option from a dropdown menu.
# We need to identify the correct option within the dropdown menu based on its value attribute.
# The dropdown menu is specified by its XPATH, and the value of the option we need to select is "2".
# We can use the following "select" XPATH to locate the dropdown menu and the value "2" to select the appropriate option:
# /html/body/div/main/form/section/div/select

- actions:
    - action:
        # Select the "3:00 AM - 4:00 AM" option by targeting the dropdown menu with the specified XPATH.
        args:
            xpath: "/html/body/div/main/form/section/div/select"
            value: "2"
        name: "dropdownSelect"
```
"""

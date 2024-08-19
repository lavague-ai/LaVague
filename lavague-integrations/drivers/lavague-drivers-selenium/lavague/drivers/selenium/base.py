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
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.destroy()

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
Always target elements by using the full XPATH. You can only use one of the Xpaths included in the HTML. Do not derive new Xpaths.

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

Here are examples of previous answers:
HTML:
<div class="c1ntbm87 atm_am_1pywi5l atm_jb_p59q1q atm_l8_vqrj7l atm_r3_1h6ojuz__1v156lz dir dir-ltr"><div class="l1sjr04j atm_9s_1o8liyq atm_vh_nkobfv atm_r3_1e5hqsa atm_gi_xjk4d9__1v156lz l1x4ovsg atm_tw_xchc94 atm_tw_1qred53__1v156lz llb1jct atm_vy_1osqo2v atm_tr_wkersm atm_vl_ewfl5b lc9d3st atm_uc_1vossl dir dir-ltr" data-searchbar-open="false"><div aria-labelledby="littleSearchLabel" class="chgx2vp atm_ymjvfd_8tjzot atm_cjn97f_u29brm atm_mk_h2mmj6 atm_h_1h6ojuz atm_2d_1p8m8iw atm_3f_1vlbu9m atm_5j_1ylpe5n atm_70_3to2mm atm_7l_dezgoh atm_9s_116y0ak atm_j3_1osqo2v atm_r3_1e5hqsa atm_uc_aaiy6o atm_vh_nkobfv atm_uc_glywfm__1rrf6b5 atm_70_1p8xsmn_1nos8r dir dir-ltr" data-testid="little-search" role="search" xpath="/html/body/div[5]/div/div/div/div/div[3]/header/div/div/div/div/div/div[2]/div/div"><span class="a8jt5op atm_3f_idpfg4 atm_7h_hxbz6r atm_7i_ysn8ba atm_e2_t94yts atm_ks_zryt35 atm_l8_idpfg4 atm_mk_stnw88 atm_vv_1q9ccgz atm_vy_t94yts dir dir-ltr" id="littleSearchLabel">Start your search</span><span class="ieg7dag atm_j3_1osqo2v atm_9s_116y0ak atm_h_1h6ojuz dir dir-ltr" xpath="/html/body/div[5]/div/div/div/div/div[3]/header/div/div/div/div/div/div[2]/div/div/span[2]"><button class="ffgcxut atm_1s_glywfm atm_26_1j28jx2 atm_7l_1kw7nm4 atm_9j_tlke0l atm_bx_1kw7nm4 atm_c8_1kw7nm4 atm_cs_1kw7nm4 atm_g3_1kw7nm4 atm_ks_ewfl5b atm_l8_idpfg4 atm_r3_1kw7nm4 atm_rd_glywfm atm_vb_1wugsn5 atm_kd_glywfm atm_h_1h6ojuz atm_3f_okh77k atm_5j_1y44olf atm_9s_1txwivl atm_am_1pywi5l atm_e2_fyhuej atm_gi_1n1ank9 atm_jb_idpfg4 atm_mk_h2mmj6 atm_wq_kb7nvz atm_3f_glywfm_jo46a5 atm_l8_idpfg4_jo46a5 atm_gi_idpfg4_jo46a5 atm_3f_glywfm_1icshfk atm_kd_glywfm_19774hq atm_lk_ftgil2_n9iw0w atm_6a_1kw7nm4_n9iw0w atm_43_1kw7nm4_n9iw0w atm_6c_1kw7nm4_1eiowux atm_45_1kw7nm4_1eiowux atm_70_lgq2mu_1w3cfyq atm_70_lgq2mu_pfnrn2_1oszvuo dir dir-ltr" data-index="0" data-testid="little-search-location" type="button" xpath="/html/body/div[5]/div/div/div/div/div[3]/header/div/div/div/div/div/div[2]/div/div/span[2]/button"><span class="a8jt5op atm_3f_idpfg4 atm_7h_hxbz6r atm_7i_ysn8ba atm_e2_t94yts atm_ks_zryt35 atm_l8_idpfg4 atm_mk_stnw88 atm_vv_1q9ccgz atm_vy_t94yts dir dir-ltr">Location</span><div class="f16sug5q atm_c8_1cw7z3g atm_g3_qslrf5 atm_cs_10d11i2 atm_l8_1mni9fk atm_sq_1l2sidv atm_vv_1q9ccgz atm_ks_15vqwwr atm_am_ggq5uc atm_jb_1xtcb10 dir dir-ltr" xpath="/html/body/div[5]/div/div/div/div/div[3]/header/div/div/div/div/div/div[2]/div/div/span[2]/button/div">Perros-Guirec</div></button><span class="d242rgr atm_2d_1oqmvsg atm_am_9h6r71 atm_e2_1tcgj5g atm_vy_t94yts dir dir-ltr"></span><button class="ffgcxut atm_1s_glywfm atm_26_1j28jx2 atm_7l_1kw7nm4 atm_9j_tlke0l atm_bx_1kw7nm4 atm_c8_1kw7nm4 atm_cs_1kw7nm4 atm_g3_1kw7nm4 atm_ks_ewfl5b atm_l8_idpfg4 atm_r3_1kw7nm4 atm_rd_glywfm atm_vb_1wugsn5 atm_kd_glywfm atm_h_1h6ojuz atm_3f_okh77k atm_5j_1y44olf atm_9s_1txwivl atm_am_1pywi5l atm_e2_fyhuej atm_gi_1n1ank9 atm_jb_idpfg4 atm_mk_h2mmj6 atm_wq_kb7nvz atm_3f_glywfm_jo46a5 atm_l8_idpfg4_jo46a5 atm_gi_idpfg4_jo46a5 atm_3f_glywfm_1icshfk atm_kd_glywfm_19774hq atm_lk_ftgil2_n9iw0w atm_6a_1kw7nm4_n9iw0w atm_43_1kw7nm4_n9iw0w atm_6c_1kw7nm4_1eiowux atm_45_1kw7nm4_1eiowux atm_70_lgq2mu_1w3cfyq atm_70_lgq2mu_pfnrn2_1oszvuo dir dir-ltr" data-index="1" data-testid="little-search-date" type="button" xpath="/html/body/div[5]/div/div/div/div/div[3]/header/div/div/div/div/div/div[2]/div/div/span[2]/button[2]"><span class="a8jt5op atm_3f_idpfg4 atm_7h_hxbz6r atm_7i_ysn8ba atm_e2_t94yts atm_ks_zryt35 atm_l8_idpfg4 atm_mk_stnw88 atm_vv_1q9ccgz atm_vy_t94yts dir dir-ltr">Check in / Check out</span>
<div class="d7azc6i atm_9s_1txwivl atm_ks_15vqwwr atm_le_1fwxnve atm_j3_4bvhms atm_ks_zryt35__1rgatj2 dir dir-ltr"><div class="d1vla4cf atm_h_esu3gu atm_9s_1txwivl atm_fc_1h6ojuz atm_ge_glywfm atm_gi_idpfg4 atm_l8_idpfg4 atm_uc_15j2ivy atm_uc_glywfm__1rrf6b5 dhwpulo atm_tr_5qhi5r dir dir-ltr" style="--dls-indicatordots-container-transform: translateX(0px);"><span class="d1g6z6mb atm_5j_1ssbidh atm_uc_ik60j0 atm_e2_i2wt44 atm_gz_71o5yt atm_h0_71o5yt atm_jb_i2wt44 atm_vy_i2wt44 atm_uc_glywfm__1rrf6b5 d2u4fye atm_26_1kak6b4 sok0i1f atm_tr_dcem3k dir dir-ltr" style="--dls-indicatordots-dot-transform: scale(1);"></span><span class="d1g6z6mb atm_26_k5743w atm_5j_1ssbidh atm_uc_ik60j0 atm_e2_i2wt44 atm_gz_71o5yt atm_h0_71o5yt atm_jb_i2wt44 atm_vy_i2wt44 atm_uc_glywfm__1rrf6b5 sok0i1f atm_tr_dcem3k dir dir-ltr" style="--dls-indicatordots-dot-transform: scale(1);"></span><span class="d1g6z6mb atm_26_k5743w atm_5j_1ssbidh atm_uc_ik60j0 atm_e2_i2wt44 atm_gz_71o5yt atm_h0_71o5yt atm_jb_i2wt44 atm_vy_i2wt44 atm_uc_glywfm__1rrf6b5 sok0i1f atm_tr_dcem3k dir dir-ltr" style="--dls-indicatordots-dot-transform: scale(1);"></span><span class="d1g6z6mb atm_26_k5743w atm_5j_1ssbidh atm_uc_ik60j0 atm_e2_i2wt44 atm_gz_71o5yt atm_h0_71o5yt atm_jb_i2wt44 atm_vy_i2wt44 atm_uc_glywfm__1rrf6b5 sok0i1f atm_tr_dcem3k dir dir-ltr" style="--dls-indicatordots-dot-transform: scale(0.8333333333333334);"></span><span class="d1g6z6mb atm_26_k5743w atm_5j_1ssbidh atm_uc_ik60j0 atm_e2_i2wt44 atm_gz_71o5yt atm_h0_71o5yt atm_jb_i2wt44 atm_vy_i2wt44 atm_uc_glywfm__1rrf6b5 sok0i1f atm_tr_dcem3k dir dir-ltr" style="--dls-indicatordots-dot-transform: scale(0.6666666666666666);"></span><span class="d1g6z6mb atm_26_k5743w atm_5j_1ssbidh atm_uc_ik60j0 atm_e2_i2wt44 atm_gz_71o5yt atm_h0_71o5yt atm_jb_i2wt44 atm_vy_i2wt44 atm_uc_glywfm__1rrf6b5 sok0i1f atm_tr_dcem3k dir dir-ltr" style="--dls-indicatordots-dot-transform: scale(0.6666666666666666);"></span></div></div></div></div><div class="b18glxm4 atm_fg_esu3gu dir dir-ltr"></div></div></div></div><div class="s1yvqyx7 atm_d2_1mxew8z atm_gp_1rldl0o atm_go_1kc7gxz atm_gy_1gdueyf atm_gx_1q7iut atm_mh_k8b3f6 atm_l8_55ikqx dir dir-ltr"><div class="dir dir-ltr"><div class="awuxh4x atm_1w_12kg1i__4c1lm5 atm_lo_1auwtbz__320uii atm_mk_hqdblt__320uii dir dir-ltr"><div class="cw9aemg atm_e2_1osqo2v atm_jb_idpfg4 atm_mk_n7od8j atm_mk_stnw88__320uii atm_e2_1osqo2v__320uii atm_vy_1osqo2v__320uii atm_tk_idpfg4__320uii atm_fq_idpfg4__320uii atm_n3_idpfg4__320uii atm_6i_idpfg4__320uii dir dir-ltr"><div class="c14whb16 atm_8w_je46wd atm_90_wqqh0j atm_93_16tozh0 atm_9s_11p5wf0 atm_d5_1bp4okc atm_d3_8n3s54 atm_cx_dfedth atm_e0_1fe5oxz atm_dy_kim48s atm_fc_1y6m0gg atm_gi_idpfg4 atm_j6_mtsehg atm_e2_1kjme8w atm_ks_ndwtr5 atm_l4_1f51e7f atm_ld_5ul63a atm_lc_djs5a5 atm_lj_wg387a atm_li_1y0adu4 atm_o3_1p5gfer atm_p9_glywfm atm_tl_19lnvtn atm_or_dhnz5w__ta18iu atm_9s_glywfm_14pyf7n atm_oa_2geptf_bqoj1z atm_oq_1vwytc5_bqoj1z dir dir-ltr" xpath="/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div/div/div/div/div/div[2]/div/div/div/div"><a aria-hidden="true" class="rfexzly atm_9s_1ulexfb atm_7l_1j28jx2 atm_e2_1osqo2v dir dir-ltr" href="/rooms/48556008?adults=2&amp;search_mode=regular_search&amp;check_in=2024-08-15&amp;check_out=2024-08-22&amp;source_impression_id=p3_1723635992_P3MzbceR_yoTqlYM&amp;previous_page_section_name=1000&amp;federated_search_id=5176deef-4781-4419-99e0-f3624633cbd3" rel="noopener noreferrer nofollow" style="outline: red dashed 2px; outline-offset: -1px;" tabindex="-1" target="listing_48556008"><div class="cjv59qb atm_mk_h2mmj6 atm_vy_1osqo2v atm_e2_1osqo2v dir dir-ltr" xpath="/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div/div/div/div/div/div[2]/div/div/div/div/a/div">
<div xpath="/html/body/div[5]/d iv/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div"><div xpath="/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div"><div aria-labelledby="title_48556008" class="cy5jw6o atm_5j_223wjw atm_70_87waog atm_j3_1u6x1zy atm_jb_4shrsx atm_mk_h2mmj6 atm_vy_7abht0 dir dir-ltr" data-testid="card-container" role="group" xpath="/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div"><a aria-labelledby="title_48556008" class="l1ovpqvx atm_1he2i46_1k8pnbi_10saat9 atm_yxpdqi_1pv6nv4_10saat9 atm_1a0hdzc_w1h1e8_10saat9 atm_2bu6ew_929bqk_10saat9 atm_12oyo1u_73u7pn_10saat9 atm_fiaz40_1etamxe_10saat9 bn2bl2p atm_5j_223wjw atm_9s_1ulexfb atm_e2_1osqo2v atm_fq_idpfg4 atm_mk_stnw88 atm_tk_idpfg4 atm_vy_1osqo2v atm_26_1j28jx2 atm_3f_glywfm atm_kd_glywfm atm_3f_glywfm_jo46a5 atm_l8_idpfg4_jo46a5 atm_gi_idpfg4_jo46a5 atm_3f_glywfm_1icshfk atm_kd_glywfm_19774hq atm_uc_aaiy6o_1w3cfyq_oggzyc atm_70_1b8lkes_1w3cfyq_oggzyc atm_uc_glywfm_1w3cfyq_pynvjw atm_uc_aaiy6o_pfnrn2_ivgyl9 atm_70_1b8lkes_pfnrn2_ivgyl9 atm_uc_glywfm_pfnrn2_61fwbc dir dir-ltr" href="/rooms/48556008?adults=2&amp;search_mode=regular_search&amp;check_in=2024-08-15&amp;check_out=2024-08-22&amp;source_impression_id=p3_1723635992_P3MzbceR_yoTqlYM&amp;previous_page_section_name=1000&amp;federated_search_id=5176deef-4781-4419-99e0-f3624633cbd3" rel="noopener noreferrer nofollow" target="listing_48556008"></a><div class="lxq01kf atm_9s_1txwivl atm_am_kyuy1d atm_ar_d67k9l l1tup9az atm_1p4glcj_1bp4okc dir dir-ltr" xpath="/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div/div"><div class="m1v28t5c atm_gq_1gibeiw atm_72g4pb_llf7ib atm_1mz0ff6_1lk22r2 atm_1p5rjfj_h2mmj6 dir dir-ltr"><div class="c14dgvke atm_5j_kdyw2j atm_ks_15vqwwr atm_mj_16bk9r8 atm_mk_h2mmj6 atm_2d_1k0ymf0 atm_wq_idpfg4 atm_ks_zryt35__1rgatj2 dir dir-ltr"><div aria-describedby="carousel-description" class="cnjlbcx atm_1qvjjpw_glywfm atm_1hykvs1_n7od8j atm_ej6m29_kb7nvz atm_15nrvwg_grho7r atm_1rk3ums_1osqo2v atm_za0az8_15vqwwr atm_1ujhsu9_idpfg4 atm_2i514i_oga405 atm_bno8qn_kb7nvz c1e9noat rd7fm2t atm_9s_11p5wf0 atm_dx_1orwtfw dir dir-ltr" role="group"><div class="c18vjgz6 atm_d2_12hkhw9 atm_gp_i0jujp atm_go_165lr55 atm_gy_unm2jc atm_gx_fm7pfe atm_mh_1slnvwa atm_mj_1bomifl atm_wq_1f25d1o dir dir-ltr"><div class="o47luuh atm_26_brha5h o1q97y5m atm_9s_1txwivl atm_am_kb7nvz atm_au_1bp4okc atm_tk_idpfg4 atm_fq_idpfg4 atm_n3_idpfg4 atm_6i_idpfg4 atm_ks_15vqwwr atm_l8_9yxej atm_mj_glywfm atm_mk_stnw88 atm_am_mu6cqg_13ayz6n dir dir-ltr"><div class="tsz9f4o atm_9s_11p5wf0 atm_dd_8tjzot atm_dz_fbbpjf dir dir-ltr"><div class="t1p13dzz atm_fg_1y6m0gg dir dir-ltr"><div class="f9iqyua atm_h_1h6ojuz atm_9s_116y0ak atm_cs_10d11i2 atm_e2_1ns9ob4 atm_j3_1osqo2v atm_c8_km0zk7_1m4t57z atm_fr_1m9t47k_1m4t57z atm_g3_18khvle_1m4t57z atm_ks_15vqwwr_1m4t57z atm_sq_1l2sidv_1m4t57z atm_9s_cj1kg8_1m4t57z atm_6w_1e54zos_1m4t57z atm_fy_kb7nvz_1m4t57z atm_w4_9jpisv_1m4t57z atm_ks_zryt35_1m4t57z_1rgatj2 movpp6a atm_20_jtrrsy atm_26_1wk4v4l atm_2a_usvi9m atm_5j_1ylpe5n atm_3f_1m0p167 atm_7l_985nu1 atm_l8_uxmpr7 b1b9hiva atm_h3_yh40bf dir dir-ltr" style="--formatted-badge_text-color: #FFFFFF;"><span class="a8jt5op atm_3f_idpfg4 atm_7h_hxbz6r atm_7i_ysn8ba atm_e2_t94yts atm_ks_zryt35 atm_l8_idpfg4 atm_mk_stnw88 atm_vv_1q9ccgz atm_vy_t94yts dir dir-ltr">Superhost</span><div aria-hidden="true" class="t1qa5xaj dir dir-ltr">Superhost</div></div></div><div class="ts9x1g6 atm_9s_1txwivl atm_fg_esu3gu atm_gz_19bvopo_1q27gxn dir dir-ltr">
Query: Click on 'Home in Ploubazlanec
Authorized Xpaths: "{'/html/body/div[5]/div/div/div/div/div[3]/header/div/div/div/div/div/div[2]/div/div/span[2]', '/html/body/div[5]/div/div/div/div/div[3]/header/div/div/div/div/div/div[2]/div/div', '/html/body/div[5]/d iv/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div', '/html/body/div[5]/div/div/div/div/div[3]/header/div/div/div/div/div/div[2]/div/div/span[2]/button/div', '/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div', '/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div/div/div/div/div/div[2]/div/div/div/div/a/div', '/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div', '/html/body/div[5]/div/div/div/div/div[3]/header/div/div/div/div/div/div[2]/div/div/span[2]/button[2]', '/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div/div/div/div/div/div[2]/div/div/div/div', '/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div/div', '/html/body/div[5]/div/div/div/div/div[3]/header/div/div/div/div/div/div[2]/div/div/span[2]/button'}"
Completion:
```yaml
# Let's think through this step-by-step:
# 1. The query asks us to click on 'Home in Ploubazlanec'
# 2. In the HTML, we need to find an element that represents this listing
# 3. We can see a div with the text "Home in Ploubazlanec" in the title
# 4. The parent element of this div is an anchor tag, which is likely the clickable link for the listing
# 5. We should use the XPath of this anchor tag to perform the click action

- actions:
    - action:
        # Click on the anchor tag that contains the listing title
        args:
            xpath: "/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div/div/div/div/div/div[2]/div/div/div/div/a"
        name: "click"
```
-----
HTML:
<div class="devsite-top-logo-row-middle" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]">
<div class="devsite-header-upper-tabs" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]">
<devsite-tabs class="upper-tabs devsite-overflow-menu--open" connected="" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs">
<a aria-label="Extended Navigation" class="devsite-icon devsite-icon-arrow-drop-down" href="#" style="border: 2px solid red;" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/a"><!--?lit$8296333005$-->More</a>
<div class="devsite-tabs-overflow-menu" scrollbars="" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div">
<tab xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]">
<a class="devsite-tabs-content gc-analytics-event" data-category="Site-Wide Custom Events" data-label="Tab: Gemma" href="https://ai.google.dev/gemma" track-metadata-eventdetail="https://ai.google.dev/gemma" track-metadata-module="primary nav" track-metadata-position="nav - gemma" track-name="gemma" track-type="nav" xpath="/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]/a">
Authorized Xpaths: "{'/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs', '/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/a', '/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div', '/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]/a', '/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]', '/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]', '/html/body/section/devsite-header/div/div[1]/div/div/div[2]'}"
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
Authorized Xpaths: "{'/html/body/div/main/form/section/div/select'}"
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

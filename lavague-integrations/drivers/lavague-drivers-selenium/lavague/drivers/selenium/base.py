import json
import time
from typing import Callable, Dict, List, Optional

from lavague.drivers.selenium.node import SeleniumNode
from lavague.drivers.selenium.prompt import SELENIUM_PROMPT_TEMPLATE
from lavague.sdk.base_driver import BaseDriver
from lavague.sdk.base_driver.interaction import (
    InteractionType,
    PossibleInteractionsByXpath,
    ScrollDirection,
)
from lavague.sdk.base_driver.javascript import (
    ATTACH_MOVE_LISTENER,
    JS_GET_INTERACTIVES,
    JS_GET_SCROLLABLE_PARENT,
    JS_GET_SHADOW_ROOTS,
    JS_SETUP_GET_EVENTS,
    JS_WAIT_DOM_IDLE,
    REMOVE_HIGHLIGHT,
    get_highlighter_style,
)
from lavague.sdk.exceptions import (
    CannotBackException,
    NoPageException,
)

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumDriver(BaseDriver[SeleniumNode]):
    driver: WebDriver

    def __init__(
        self,
        options: Optional[Options] = None,
        headless: bool = True,
        user_data_dir: Optional[str] = None,
        waiting_completion_timeout=10,
        log_waiting_time=False,
        user_agent="Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
        auto_init=True,
        width: int = 1096,
        height: int = 1096,
    ) -> None:
        self.waiting_completion_timeout = waiting_completion_timeout
        self.log_waiting_time = log_waiting_time
        self.width = width
        self.height = height
        if options:
            self.options = options
        else:
            self.options = Options()
            if headless:
                self.options.add_argument("--headless=new")
            self.options.add_argument("--lang=en")
            self.options.add_argument(f"user-agent={user_agent}")
            self.options.add_argument("--disable-notifications")
        if user_data_dir:
            self.options.add_argument(f"--user-data-dir={user_data_dir}")
        self.options.page_load_strategy = "normal"
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-web-security")
        self.options.add_argument("--disable-site-isolation-trials")
        self.options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        if auto_init:
            self.init()

    def init(self) -> None:
        self.driver = Chrome(options=self.options)
        self.resize_driver(self.width, self.height)
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": JS_SETUP_GET_EVENTS},
        )

    def destroy(self) -> None:
        """Cleanly destroy the underlying driver"""
        self.driver.quit()

    def resize_driver(self, width: int, height: int):
        """Resize the viewport to a targeted height and width"""
        self.driver.set_window_size(width, height)
        viewport_height = self.driver.execute_script("return window.innerHeight;")
        height_difference = height - viewport_height
        self.driver.set_window_size(width, height + height_difference)

    def get_url(self) -> str:
        """Get the url of the current page, raise NoPageException if no page is loaded"""
        if self.driver.current_url == "data:,":
            raise NoPageException()
        return self.driver.current_url

    def get(self, url: str) -> None:
        """Navigate to the url"""
        self.driver.get(url)

    def back(self) -> None:
        """Navigate back, raise CannotBackException if history root is reached"""
        if self.driver.execute_script("return !document.referrer;"):
            raise CannotBackException()
        self.driver.back()

    def get_html(self) -> str:
        """
        Returns the HTML of the current page.
        If clean is True, We remove unnecessary tags and attributes from the HTML.
        Clean HTMLs are easier to process for the LLM.
        """
        return self.driver.page_source

    def get_tabs(self) -> str:
        """Return description of the tabs opened with the current tab being focused.

        Example of output:
        Tabs opened:
        0 - Overview - OpenAI API
        1 - [CURRENT] Nos destinations Train - SNCF Connect
        """
        window_handles = self.driver.window_handles
        # Store the current window handle (focused tab)
        current_handle = self.driver.current_window_handle
        tab_info = []
        tab_id = 0

        for handle in window_handles:
            # Switch to each tab
            self.driver.switch_to.window(handle)

            # Get the title of the current tab
            title = self.driver.title

            # Check if this is the focused tab
            if handle == current_handle:
                tab_info.append(f"{tab_id} - [CURRENT] {title}")
            else:
                tab_info.append(f"{tab_id} - {title}")

            tab_id += 1

        # Switch back to the original tab
        self.driver.switch_to.window(current_handle)

        tab_info = "\n".join(tab_info)
        tab_info = "Tabs opened:\n" + tab_info
        return tab_info

    def switch_tab(self, tab_id: int) -> None:
        """Switch to the tab with the given id"""
        window_handles = self.driver.window_handles
        self.driver.switch_to.window(window_handles[tab_id])

    def type_key(self, key: str) -> None:
        """Type a key"""
        ActionChains(self.driver).send_keys(key).perform()

    def resolve_xpath(self, xpath: str):
        """
        Return the element for the corresponding xpath, the underlying driver may switch iframe if necessary
        """
        return SeleniumNode(self.driver, xpath)

    def get_viewport_size(self) -> dict:
        """Return viewport size as {"width": int, "height": int}"""
        viewport_size = {}
        viewport_size["width"] = self.driver.execute_script("return window.innerWidth;")
        viewport_size["height"] = self.driver.execute_script(
            "return window.innerHeight;"
        )
        return viewport_size

    def get_possible_interactions(
        self,
        in_viewport=True,
        foreground_only=True,
        types: List[InteractionType] = [
            InteractionType.CLICK,
            InteractionType.TYPE,
            InteractionType.HOVER,
        ],
    ) -> PossibleInteractionsByXpath:
        """Get elements that can be interacted with as a dictionary mapped by xpath"""
        exe: Dict[str, List[str]] = self.driver.execute_script(
            JS_GET_INTERACTIVES,
            in_viewport,
            foreground_only,
            False,
            [t.name for t in types],
        )
        res = dict()
        for k, v in exe.items():
            res[k] = set(InteractionType[i] for i in v)
        return res

    def scroll_into_view(self, xpath: str):
        with self.resolve_xpath(xpath) as node:
            self.driver.execute_script("arguments[0].scrollIntoView()", node.element)

    def scroll(
        self,
        xpath_anchor: Optional[str] = "/html/body",
        direction: ScrollDirection = ScrollDirection.DOWN,
        scroll_factor=0.75,
    ):
        try:
            scroll_anchor = self.get_scroll_anchor(xpath_anchor)
            if not scroll_anchor:
                self.scroll_page(direction)
                return
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
        except NoSuchElementException:
            self.scroll_page(direction)

    def scroll_page(self, direction: ScrollDirection = ScrollDirection.DOWN):
        self.driver.execute_script(direction.get_page_script())

    def get_scroll_anchor(self, xpath_anchor: Optional[str] = None) -> WebElement:
        with self.resolve_xpath(xpath_anchor or "/html/body") as element_resolved:
            element = element_resolved.element
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

    def wait_for_dom_stable(self, timeout: float = 10):
        self.driver.execute_script(JS_WAIT_DOM_IDLE, max(0, round(timeout * 1000)))

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
        """Prompt to explain the llm which style of code he should output and which variables and imports he should expect"""
        return SELENIUM_PROMPT_TEMPLATE

    def get_screenshot_as_png(self) -> bytes:
        return self.driver.get_screenshot_as_png()

    def get_shadow_roots(self) -> Dict[str, str]:
        """Return a dictionary of shadow roots HTML by xpath"""
        return self.driver.execute_script(JS_GET_SHADOW_ROOTS)

    def get_nodes(self, xpaths: List[str]) -> List[SeleniumNode]:
        return [SeleniumNode(self.driver, xpath) for xpath in xpaths]

    def highlight_nodes(
        self, xpaths: List[str], color: str = "red", label=False
    ) -> Callable:
        nodes = self.get_nodes(xpaths)
        self.driver.execute_script(ATTACH_MOVE_LISTENER)
        set_style = get_highlighter_style(color, label)
        self.exec_script_for_nodes(
            nodes, "arguments[0].forEach((a, i) => { " + set_style + "})"
        )
        return self._add_highlighted_destructors(
            lambda: self.remove_nodes_highlight(xpaths)
        )

    def remove_nodes_highlight(self, xpaths: List[str]):
        self.exec_script_for_nodes(
            self.get_nodes(xpaths),
            REMOVE_HIGHLIGHT,
        )

    def exec_script_for_nodes(self, nodes: List[SeleniumNode], script: str):
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
            # iframe and shadow DOM must use the resolve_xpath method
            for n in special_nodes:
                if n.element:
                    self.driver.execute_script(
                        script,
                        [n.element],
                    )
                    self.driver.switch_to.default_content()

    def switch_frame(self, xpath: str) -> None:
        iframe = self.driver.find_element(By.XPATH, xpath)
        self.driver.switch_to.frame(iframe)

    def switch_parent_frame(self) -> None:
        self.driver.switch_to.parent_frame()

import json
import time
from typing import Callable, Dict, List, Optional

from lavague.drivers.selenium.node import SeleniumNode
from lavague.sdk.action.navigation import NavigationOutput
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
from selenium.webdriver.support.ui import Select, WebDriverWait


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
    ) -> None:
        self.waiting_completion_timeout = waiting_completion_timeout
        self.log_waiting_time = log_waiting_time
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
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": JS_SETUP_GET_EVENTS},
        )

    def execute(self, action: NavigationOutput) -> None:
        """Execute an action"""
        with self.resolve_xpath(action.xpath) as node:
            match action.navigation_command:
                case InteractionType.CLICK:
                    node.element.click()

                case InteractionType.TYPE:
                    value = action.value or ""
                    if node.element.tag_name == "input":
                        node.element.clear()
                    if node.element.tag_name == "select":
                        select = Select(node.element)
                        try:
                            select.select_by_value(value)
                        except NoSuchElementException:
                            select.select_by_visible_text(value)
                    else:
                        node.element.send_keys(value)

                case InteractionType.HOVER:
                    ActionChains(self.driver).move_to_element(node.element).perform()

                case InteractionType.SCROLL:
                    direction = ScrollDirection.from_string(action.value or "DOWN")
                    self.scroll(action.xpath, direction)

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
<div>Check in / Check out</div>
<div xpath="/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div/div/div/div/div/div[2]/div/div/div/div"><a aria-hidden="true" href="/rooms/48556008?adults=2&amp;search_mode=regular_search&amp;check_in=2024-08-15&amp;check_out=2024-08-22" rel="noopener noreferrer nofollow" tabindex="-1" target="listing_48556008"><div class="dir dir-ltr" xpath="/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div/div/div/div/div/div[2]/div/div/div/div/a/div">
<div xpath="/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div"><div xpath="/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div"><div aria-labelledby="title_48556008" data-testid="card-container" role="group" xpath="/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div"><a aria-labelledby="title_48556008" href="/rooms/48556008?adults=2&amp;search_mode=regular_search&amp;check_in=2024-08-15&amp;check_out=2024-08-22" rel="noopener noreferrer nofollow" target="listing_48556008"></a><div xpath="/html/body/div[5]/div/div/div/div/div[3]/div/main/div[2]/div/div[2]/div/div/div/div/div/div/div/div[2]/div/div/div/div/div">
Query: Click on 'Home in Ploubazlanec'
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

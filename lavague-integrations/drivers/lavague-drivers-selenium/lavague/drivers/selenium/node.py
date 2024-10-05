import re
from io import BytesIO
from typing import Optional

from lavague.sdk.base_driver import DOMNode
from lavague.sdk.exceptions import ElementNotFoundException
from PIL import Image

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.shadowroot import ShadowRoot
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select


class SeleniumNode(DOMNode[WebElement]):
    def __init__(
        self,
        driver: WebDriver,
        xpath: str,
        element: Optional[WebElement] = None,
    ) -> None:
        self.driver = driver
        self.xpath = xpath
        if element:
            self._element = element
        super().__init__()

    @property
    def element(self) -> WebElement:
        if not hasattr(self, "_element"):
            print("WARN: DOMNode context manager missing")
            self.__enter__()
        if self._element is None:
            raise ElementNotFoundException(self.xpath)
        return self._element

    @property
    def value(self) -> Optional[str]:
        return self.element.get_attribute("value")

    @property
    def text(self) -> str:
        return self.driver.execute_script(
            "return arguments[0].textContent", self.element
        )

    @property
    def outer_html(self) -> str:
        return self.driver.execute_script("return arguments[0].outerHTML", self.element)

    @property
    def inner_html(self) -> str:
        return self.driver.execute_script("return arguments[0].innerHTML", self.element)

    def take_screenshot(self):
        with self:
            if self.element:
                try:
                    return Image.open(BytesIO(self.element.screenshot_as_png))
                except WebDriverException:
                    pass
        return Image.new("RGB", (0, 0))

    def click(self):
        with self:
            try:
                self.element.click()
            except ElementClickInterceptedException:
                try:
                    # Move to the element and click at its position
                    ActionChains(self.driver).move_to_element(
                        self.element
                    ).click().perform()
                except Exception as click_error:
                    raise Exception(
                        f"Failed to click at element coordinates of {self.xpath} : {str(click_error)}"
                    )

    def set_value(self, value: str):
        with self:
            if self.element.tag_name == "input":
                try:
                    self.element.clear()
                except WebDriverException:
                    pass
            if self.element.tag_name == "select":
                select = Select(self.element)
                try:
                    select.select_by_value(value)
                except NoSuchElementException:
                    select.select_by_visible_text(value)
            else:
                self.click()
                (
                    ActionChains(self.driver)
                    .key_down(Keys.CONTROL)
                    .send_keys("a")
                    .key_up(Keys.CONTROL)
                    .send_keys(Keys.DELETE)  # clear the input field
                    .send_keys(value)
                    .perform()
                )

    def hover(self):
        with self:
            ActionChains(self.driver).move_to_element(self.element).perform()

    def enter_context(self):
        if hasattr(self, "_element"):
            return

        root = self.driver
        local_xpath = self.xpath

        def find_element(xpath):
            try:
                if isinstance(root, ShadowRoot):
                    # Shadow root does not support find_element with xpath
                    css_selector = re.sub(
                        r"\[([0-9]+)\]",
                        r":nth-of-type(\1)",
                        xpath[1:].replace("/", " > "),
                    )
                    return root.find_element(By.CSS_SELECTOR, css_selector)
                return root.find_element(By.XPATH, xpath)
            except Exception:
                return None

        while local_xpath:
            match = re.search(r"/iframe|//", local_xpath)

            if match:
                before, sep, local_xpath = local_xpath.partition(match.group())
                if sep == "/iframe":
                    iframe = self.driver.find_element(By.XPATH, before + sep)
                    self.driver.switch_to.frame(iframe)
                elif sep == "//":
                    custom_element = find_element(before)
                    if not custom_element:
                        break
                    root = custom_element.shadow_root
                    local_xpath = "/" + local_xpath
            else:
                break

        self._element = find_element(local_xpath)

        if not self._element:
            raise ElementNotFoundException(self.xpath)

    def exit_context(self):
        if hasattr(self, "_element"):
            self.driver.switch_to.default_content()
            del self._element

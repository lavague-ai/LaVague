from abc import ABC, abstractmethod
from typing import Any
from selenium.webdriver.remote.webdriver import WebDriver
from .format_utils import clean_html


class AbstractDriver(ABC):
    def getDriver(self) -> Any:
        pass

    @abstractmethod
    def getUrl(self) -> str:
        pass

    @abstractmethod
    def goTo(self, url: str) -> None:
        pass

    @abstractmethod
    def getHtml(self, clean: bool = True) -> str:
        """
        Returns the HTML of the current page.
        If clean is True, We remove unnecessary tags and attributes from the HTML.
        Clean HTMLs are easier to process for the LLM.
        """
        pass

    @abstractmethod
    def getScreenshot(self, url: str, filename: str) -> None:
        pass

    @abstractmethod
    def destroy(self) -> None:
        pass


class SeleniumDriver(AbstractDriver):
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def getDriver(self) -> Any:
        return self.driver

    def getUrl(self) -> str:
        return self.driver.current_url

    def goTo(self, url: str) -> None:
        self.driver.get(url)

    def getHtml(self, clean: bool = True) -> str:
        html = self.driver.page_source
        return clean_html(html) if clean else html

    def getScreenshot(self, filename: str) -> None:
        self.driver.save_screenshot(filename)

    def destroy(self) -> None:
        self.driver.quit()

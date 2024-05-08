from abc import ABC, abstractmethod
from typing import Any, Tuple
from .format_utils import clean_html

try:
    from selenium.webdriver.remote.webdriver import WebDriver

    SELENIUM_IMPORT = True
except:
    SELENIUM_IMPORT = False

try:
    from playwright.sync_api import Page
    from playwright.sync_api._generated import Playwright

    PLAYWRIGHT_IMPORT = True
except:
    PLAYWRIGHT_IMPORT = False


class AbstractDriver(ABC):
    def getDriver(self) -> Tuple[str, Any]:
        """Return the expected variable name and the driver object"""
        pass

    @abstractmethod
    def getUrl(self) -> str:
        """Get the url of the current page"""
        pass

    @abstractmethod
    def goToUrlCode(self, url: str) -> str:
        """Return the code to navigate to the url"""
        pass

    @abstractmethod
    def goTo(self, url: str) -> None:
        """Navigate to the url"""
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
    def getScreenshot(self, filename: str) -> None:
        """Save a screenshot to the file filename"""
        pass

    @abstractmethod
    def getDummyCode(self) -> str:
        """Return testing code relevant for the current driver"""

    pass

    @abstractmethod
    def destroy(self) -> None:
        """Cleanly destroy the underlying driver"""
        pass


if SELENIUM_IMPORT:

    class SeleniumDriver(AbstractDriver):
        def __init__(self, selenium_driver: WebDriver):
            self.driver = selenium_driver

        def getDriver(self) -> Tuple[str, WebDriver]:
            return "driver", self.driver

        def getUrl(self) -> str:
            return self.driver.current_url

        def goToUrlCode(self, url: str) -> str:
            return f'driver.get("{url}")'

        def goTo(self, url: str) -> None:
            self.driver.get(url)

        def getHtml(self, clean: bool = True) -> str:
            html = self.driver.page_source
            return clean_html(html) if clean else html

        def getScreenshot(self, filename: str) -> None:
            self.driver.save_screenshot(filename)

        def getDummyCode(self) -> str:
            return 'driver.execute_script("window.scrollBy(0, 500)")'

        def destroy(self) -> None:
            self.driver.quit()


if PLAYWRIGHT_IMPORT:

    class PlaywrightDriver(AbstractDriver):
        def __init__(self, sync_playwright_page: Page, context: Playwright):
            self.driver = sync_playwright_page
            self.context = context

        def getDriver(self) -> Tuple[str, Page]:
            return "page", self.driver

        def getUrl(self) -> str:
            return self.driver.url

        def goToUrlCode(self, url: str) -> str:
            return f'page.goto("{url}")'

        def goTo(self, url: str) -> None:
            return self.driver.goto(url)

        def getHtml(self) -> str:
            return self.driver.content()

        def getScreenshot(self, filename: str) -> None:
            return self.driver.screenshot(path=filename)

        def getDummyCode(self) -> str:
            return "page.mouse.wheel(delta_x=0, delta_y=500)"

        def destroy(self) -> None:
            self.driver.close()
            self.context.stop()

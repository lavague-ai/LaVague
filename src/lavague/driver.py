from abc import ABC, abstractmethod
from typing import Any
from .format_utils import clean_html


try:
    from selenium.webdriver.remote.webdriver import WebDriver
    SELENIUM_IMPORT = True
except:
    SELENIUM_IMPORT = False

try:
    from playwright.sync_api import Page
    PLAYWRIGHT_IMPORT = True
except:
    PLAYWRIGHT_IMPORT = False


class AbstractDriver(ABC):
    def getDriver(self) -> tuple[str, Any]:
        """Return the expected variable name and the driver object"""
        pass

    @abstractmethod
    def getUrl(self) -> str:
        pass

    @abstractmethod
    def goToUrlCode(self, url: str) -> str:
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
    def getScreenshot(self, filename: str) -> None:
        pass

    @abstractmethod
    def destroy(self) -> None:
        pass


class SeleniumDriver(AbstractDriver):
    def __init__(self, selenium_driver: WebDriver):
        if not SELENIUM_IMPORT:
            raise ImportError(
                "Selenium is not installed, install it using our setup.sh script or use our dev-env / docker image"
            )
        self.driver = selenium_driver

    def getDriver(self) -> tuple[str, WebDriver]:
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

    def destroy(self) -> None:
        self.driver.quit()


class PlaywrightDriver(AbstractDriver):
    def __init__(self, sync_playwright_page: Page):
        if not PLAYWRIGHT_IMPORT:
            raise ImportError(
                "Please install playwright using `pip install playwright` and then `playwright install` to install the necessary browser drivers"
            )
        self.driver = sync_playwright_page

    def getDriver(self) -> tuple[str, Page]:
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

    def destroy(self) -> None:
        self.driver.close()

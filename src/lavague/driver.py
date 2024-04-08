from abc import ABC, abstractmethod
from typing import Any
from selenium.webdriver.remote.webdriver import WebDriver


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
    def getHtml(self) -> str:
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

    def getHtml(self) -> str:
        return self.driver.page_source

    def getScreenshot(self, filename: str) -> None:
        self.driver.save_screenshot(filename)

    def destroy(self) -> None:
        self.driver.quit()

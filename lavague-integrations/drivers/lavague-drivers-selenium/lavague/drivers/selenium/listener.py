from selenium.webdriver.remote.webdriver import WebDriver
from lavague.core.listener import EventListener as BaseEventListener


class EventListener(BaseEventListener):
    def __init__(self, driver: WebDriver):
        super().__init__(
            lambda script, prevent_action, xpaths: driver.execute_async_script(
                script, prevent_action, xpaths
            )
        )

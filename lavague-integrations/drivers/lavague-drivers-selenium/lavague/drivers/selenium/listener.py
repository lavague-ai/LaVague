from selenium.webdriver.remote.webdriver import WebDriver
from typing import Callable
import threading


class EventListener:
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def listen_for_action(self):
        event_data = self.driver.execute_async_script(JS_LISTEN_ACTION)
        return event_data

    def listen_for_action_async(self, callback: Callable):
        thread = threading.Thread(target=lambda: callback(self.listen_for_action()))
        thread.start()


JS_LISTEN_ACTION = """
const callback = arguments[arguments.length - 1];
function handleEvent(event) {
    callback({eventType: event.type, key: event.key, button: event.button});
}
document.addEventListener('click', handleEvent);
document.addEventListener('keydown', handleEvent);
"""

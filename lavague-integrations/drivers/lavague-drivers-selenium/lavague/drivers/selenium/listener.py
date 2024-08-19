from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Callable, Any, List
import threading

JS_LISTEN_ACTION = """
function getElementXPath(element) {
    if (element === document.body) return '/html/body';
    for (let i = 0, ix = 0; i < element.parentNode.childNodes.length; i++) {
        const sibling = element.parentNode.childNodes[i];
        if (sibling === element) {
            const tagName = element.tagName.toLowerCase();
            const position = ix ? `[${ix + 1}]` : '';
            const parentPath = getElementXPath(element.parentNode);
            return `${parentPath}/${tagName}${position}`;
        }
        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) ix++;
    }
}
const listenFor = Array.isArray(arguments?.[0]) ? arguments[0] : null;
const callback = arguments[arguments.length - 1];
function handleEvent(event) {
    const xpath = getElementXPath(event.target);
    if (listenFor && !listenFor.includes(xpath)) return true;
    callback({eventType: event.type, key: event.key, button: event.button, xpath, element: event.target});
    event.preventDefault();
    event.stopPropagation();
    document.removeEventListener('click', handleEvent);
    document.removeEventListener('keydown', handleEvent);
    return false;
}
document.addEventListener('click', handleEvent);
document.addEventListener('keydown', handleEvent);
"""


class EventListener:
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def listen_next_action(self, xpaths: List[str] = None, no_timeout=False):
        try:
            event_data = self.driver.execute_async_script(JS_LISTEN_ACTION, xpaths)
            return event_data
        except TimeoutException as e:
            if no_timeout:
                return self.listen_next_action(xpaths, no_timeout)
            raise e

    def listen_next_action_async(self, callback: Callable):
        thread = threading.Thread(target=lambda: callback(self.listen_next_action()))
        thread.start()

    def listen(self, callback: Callable[[Any], bool]):
        active = True

        def destructor():
            nonlocal active
            active = False

        def loop():
            while active:
                try:
                    next = self.listen_next_action()
                    if active:
                        callback(next)
                except TimeoutException:
                    continue

        thread = threading.Thread(target=loop)
        thread.start()
        return destructor

from selenium.common.exceptions import TimeoutException
from typing import Callable, Any, List, Dict, Literal
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
    event.preventDefault();
    event.stopPropagation();
    console.log(xpath, event);
    callback({eventType: event.type, key: event.key, button: event.button, xpath, element: event.target});
    return false;
}
document.addEventListener('click', handleEvent, {capture: true, once: true});
"""


class EventListener:
    """
    A utility class for listening to DOM events using a JS executor.

    This class provides methods to listen for specific user actions (like clicks) on web elements
    identified by their XPath and execute a callback function upon detection.
    """

    def __init__(self, executor: Callable[[str, Any], Any]):
        self.executor = executor
        self._destructors = []

    def listen_next_action(
        self, xpaths: List[str] = None, no_timeout=False
    ) -> Dict[Literal["eventType", "key", "button", "xpath", "element"], Any]:
        """
        Listens for the next user action (such as a click) on elements that match the given xpaths, and prevent default behaviour.
        This method blocks until an action is detected or a timeout occurs, unless no_timeout is set to True.
        If xpaths is None all actions will be listened for.
        Returns a dictionary containing information about the detected action.
        """
        try:
            event_data = self.executor(JS_LISTEN_ACTION, xpaths)
            return event_data
        except TimeoutException as e:
            if no_timeout:
                return self.listen_next_action(xpaths, no_timeout)
            raise e

    def listen_next_action_async(
        self, callback: Callable, xpaths: List[str] = None, no_timeout=False
    ):
        """
        Same as listen_next_action but async with a callback.
        """
        thread = threading.Thread(
            target=lambda: callback(
                self.listen_next_action(xpaths=xpaths, no_timeout=no_timeout)
            )
        )
        thread.start()

    def listen(self, callback: Callable[[Any], bool]):
        """
        Listen for user actions and execute the provided callback until the listener is stopped.
        Returns a destructor function that can be used to stop listening for events.
        """
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
            self._destructors.remove(destructor)

        thread = threading.Thread(target=loop)
        thread.start()

        self._destructors.append(destructor)
        return destructor

    def stop(self):
        for destructor in self._destructors:
            destructor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

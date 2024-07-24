from PIL import Image
import os
from pathlib import Path
import re
from typing import Any, Callable, Optional, Mapping, Dict, Set, List, Union
from abc import ABC, abstractmethod
from lavague.core.utilities.format_utils import (
    extract_code_from_funct,
    extract_imports_from_lines,
)
from enum import Enum
import time
from datetime import datetime
import hashlib


class InteractionType(Enum):
    CLICK = "click"
    HOVER = "hover"
    SCROLL = "scroll"
    TYPE = "type"


PossibleInteractionsByXpath = Dict[str, Set[InteractionType]]

r_get_xpaths_from_html = r'xpath=["\'](.*?)["\']'


class BaseDriver(ABC):
    def __init__(self, url: Optional[str], init_function: Optional[Callable[[], Any]]):
        """Init the driver with the init funtion, and then go to the desired url"""
        self.init_function = (
            init_function if init_function is not None else self.default_init_code
        )
        self.driver = self.init_function()

        # Flag to check if the page has been previously scanned to avoid erasing screenshots from previous scan
        self.previously_scanned = False

        # extract import lines for later exec of generated code
        init_lines = extract_code_from_funct(self.init_function)
        self.import_lines = extract_imports_from_lines(init_lines)

        if url is not None:
            self.get(url)

    @abstractmethod
    def default_init_code(self) -> Any:
        """Init the driver, with the imports, since it will be pasted to the beginning of the output"""
        pass

    @abstractmethod
    def code_for_init(self) -> str:
        """Extract the code to past to the begining of the final script from the init code"""
        pass

    @abstractmethod
    def destroy(self) -> None:
        """Cleanly destroy the underlying driver"""
        pass

    @abstractmethod
    def get_driver(self) -> Any:
        """Return the expected variable name and the driver object"""
        pass

    @abstractmethod
    def resize_driver(driver, width, height):
        """
        Resize the driver to a targeted height and width.
        """

    @abstractmethod
    def get_url(self) -> Optional[str]:
        """Get the url of the current page"""
        pass

    @abstractmethod
    def get(self, url: str) -> None:
        """Navigate to the url"""
        pass

    @abstractmethod
    def code_for_get(self, url: str) -> str:
        """Return the code to navigate to the url"""
        pass

    @abstractmethod
    def back(self) -> None:
        """Navigate back"""
        pass

    @abstractmethod
    def maximize_window(self) -> None:
        pass

    @abstractmethod
    def code_for_back(self) -> None:
        """Return driver specific code for going back"""
        pass

    @abstractmethod
    def get_html(self, clean: bool = True) -> str:
        """
        Returns the HTML of the current page.
        If clean is True, We remove unnecessary tags and attributes from the HTML.
        Clean HTMLs are easier to process for the LLM.
        """
        pass

    def get_tabs(self) -> str:
        """Return description of the tabs opened with the current tab being focused.

        Example of output:
        Tabs opened:
        0 - Overview - OpenAI API
        1 - [CURRENT] Nos destinations Train - SNCF Connect
        """
        return "Tabs opened:\n 0 - [CURRENT] tab"

    def switch_tab(self, tab_id: int) -> None:
        """Switch to the tab with the given id"""
        pass

    def switch_frame(self, xpath) -> None:
        """
        switch to the frame pointed at by the xpath
        """
        raise NotImplementedError()

    def switch_default_frame(self) -> None:
        """
        Switch back to the default frame
        """
        raise NotImplementedError()

    def switch_parent_frame(self) -> None:
        """
        Switch back to the parent frame
        """
        raise NotImplementedError()

    def resolve_xpath(self, xpath):
        """
        Return the element for the corresponding xpath, the underlying driver may switch iframe if necessary
        """
        pass

    def save_screenshot(self, current_screenshot_folder: Path) -> str:
        """Save the screenshot data to a file and return the path. If the screenshot already exists, return the path. If not save it to the folder."""

        new_screenshot = self.get_screenshot_as_png()
        hasher = hashlib.md5()
        hasher.update(new_screenshot)
        new_hash = hasher.hexdigest()
        new_screenshot_name = f"{new_hash}.png"
        new_screenshot_full_path = current_screenshot_folder / new_screenshot_name

        # If the screenshot does not exist, save it
        if not new_screenshot_full_path.exists():
            with open(new_screenshot_full_path, "wb") as f:
                f.write(new_screenshot)
        return str(new_screenshot_full_path)

    def is_bottom_of_page(self) -> bool:
        return self.execute_script(
            "return (window.innerHeight + window.scrollY) >= document.body.scrollHeight;"
        )

    def get_screenshots_whole_page(self) -> list[str]:
        """Take screenshots of the whole page"""
        screenshot_paths = []

        current_screenshot_folder = self.get_current_screenshot_folder()

        while True:
            # Saves a screenshot
            screenshot_path = self.save_screenshot(current_screenshot_folder)
            screenshot_paths.append(screenshot_path)
            self.execute_script("window.scrollBy(0, (window.innerHeight / 1.5));")
            time.sleep(0.5)

            if self.is_bottom_of_page():
                break

        self.previously_scanned = True
        return screenshot_paths

    @abstractmethod
    def get_possible_interactions(
        self, in_viewport=True, foreground_only=True
    ) -> PossibleInteractionsByXpath:
        """Get elements that can be interacted with as a dictionary mapped by xpath"""
        pass

    def check_visibility(self, xpath: str) -> bool:
        pass

    @abstractmethod
    def get_highlighted_element(self, generated_code: str):
        """Return the page elements that generated code interact with"""
        pass

    @abstractmethod
    def exec_code(
        self,
        code: str,
        globals: dict[str, Any] = None,
        locals: Mapping[str, object] = None,
    ):
        """Exec generated code"""
        pass

    @abstractmethod
    def execute_script(self, js_code: str) -> Any:
        """Exec js script in DOM"""
        pass

    @abstractmethod
    def scroll_up(self):
        pass

    @abstractmethod
    def scroll_down(self):
        pass

    @abstractmethod
    def code_for_execute_script(self, js_code: str):
        """return driver specific code to execute js script in DOM"""
        pass

    @abstractmethod
    def get_capability(self) -> str:
        """Prompt to explain the llm which style of code he should output and which variables and imports he should expect"""
        pass

    def get_obs(self) -> dict:
        """Get the current observation of the driver"""
        current_screenshot_folder = self.get_current_screenshot_folder()

        if not self.previously_scanned:
            # If the last operation was not to scan the whole page, we clear the screenshot folder
            try:
                if os.path.isdir(current_screenshot_folder):
                    for filename in os.listdir(current_screenshot_folder):
                        file_path = os.path.join(current_screenshot_folder, filename)
                        try:
                            # Check if it's a file and then delete it
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.remove(file_path)
                        except Exception as e:
                            print(f"Failed to delete {file_path}. Reason: {e}")

            except Exception as e:
                raise Exception(f"Error while clearing screenshot folder: {e}")
        else:
            # If the last operation was to scan the whole page, we reset the flag
            self.previously_scanned = False

        # We take a screenshot and computes its hash to see if it already exists
        self.save_screenshot(current_screenshot_folder)

        url = self.get_url()
        html = self.get_html()
        obs = {
            "html": html,
            "screenshots_path": str(current_screenshot_folder),
            "url": url,
            "date": datetime.now().isoformat(),
            "tab_info": self.get_tabs(),
        }

        return obs

    def wait(self, duration):
        import time

        time.sleep(duration)

    def get_current_screenshot_folder(self) -> Path:
        url = self.get_url()
        screenshots_path = Path("./screenshots")
        screenshots_path.mkdir(exist_ok=True)

        current_url = url.replace("://", "_").replace("/", "_")
        hasher = hashlib.md5()
        hasher.update(current_url.encode("utf-8"))

        current_screenshot_folder = screenshots_path / hasher.hexdigest()
        current_screenshot_folder.mkdir(exist_ok=True)
        return current_screenshot_folder

    @abstractmethod
    def get_screenshot_as_png(self) -> bytes:
        pass

    def get_nodes(self, xpaths: List[str]) -> List["DOMNode"]:
        raise NotImplementedError("get_nodes not implemented")

    def get_nodes_from_html(self, html: str) -> List["DOMNode"]:
        return self.get_nodes(re.findall(r_get_xpaths_from_html, html))

    def highlight_node_from_xpath(self, xpath: str, color: str = "red") -> Callable:
        return self.highlight_nodes([xpath], color)

    def highlight_nodes(self, xpaths: List[str], color: str = "red") -> Callable:
        nodes = [n.highlight(color) for n in self.get_nodes(xpaths)]
        return self._add_highlighted_destructors(lambda: [n.clear() for n in nodes])

    def highlight_nodes_from_html(self, html: str, color: str = "blue") -> Callable:
        return self.highlight_nodes(re.findall(r_get_xpaths_from_html, html), color)

    def remove_highlight(self):
        if hasattr(self, "_highlight_destructors"):
            for destructor in self._highlight_destructors:
                destructor()
            delattr(self, "_highlight_destructors")

    def _add_highlighted_destructors(
        self, destructors: Union[List[Callable], Callable]
    ):
        if not hasattr(self, "_highlight_destructors"):
            self._highlight_destructors = []
        if isinstance(destructors, Callable):
            self._highlight_destructors.append(destructors)
        else:
            self._highlight_destructors.extend(destructors)
        return destructors

    def highlight_interactive_nodes(
        self,
        *with_interactions: tuple[InteractionType],
        color: str = "red",
        in_viewport=True,
        foreground_only=True,
    ):
        if with_interactions is None or len(with_interactions) == 0:
            return self.highlight_nodes(
                list(
                    self.get_possible_interactions(
                        in_viewport=in_viewport, foreground_only=foreground_only
                    ).keys()
                ),
                color,
            )

        return self.highlight_nodes(
            [
                xpath
                for xpath, interactions in self.get_possible_interactions(
                    in_viewport=in_viewport, foreground_only=foreground_only
                ).items()
                if set(interactions) & set(with_interactions)
            ],
            color,
        )


class DOMNode(ABC):
    @abstractmethod
    def highlight(self, color: str = "red"):
        pass

    @abstractmethod
    def clear(self):
        return self

    @abstractmethod
    def take_screenshot(self) -> Image:
        pass

    @abstractmethod
    def get_html(self) -> str:
        pass

    def __str__(self) -> str:
        return self.get_html()


def js_wrap_function_call(fn: str):
    return "(function(){" + fn + "})()"


JS_SETUP_GET_EVENTS = """
(function() {
  if (window && !window.getEventListeners) {
    const targetProto = EventTarget.prototype;
    targetProto._addEventListener = Element.prototype.addEventListener;
    targetProto.addEventListener = function(a,b,c) {
        this._addEventListener(a,b,c);
        if(!this.eventListenerList) this.eventListenerList = {};
        if(!this.eventListenerList[a]) this.eventListenerList[a] = [];
        this.eventListenerList[a].push(b);
    };
    targetProto._removeEventListener = Element.prototype.removeEventListener;
    targetProto.removeEventListener = function(a, b, c) {
        this._removeEventListener(a, b, c);
        if(this.eventListenerList && this.eventListenerList[a]) {
        const index = this.eventListenerList[a].indexOf(b);
        if (index > -1) {
            this.eventListenerList[a].splice(index, 1);
            if(!this.eventListenerList[a].length) {
            delete this.eventListenerList[a];
            }
        }
        }
    };
    window.getEventListeners = function(e) {
      return (e && e.eventListenerList) || [];
    }
  }
})();"""

JS_GET_INTERACTIVES = """
return (function() {
    function getInteractions(e) {
        const tag = e.tagName.toLowerCase();
        if (!e.checkVisibility() || e.hasAttribute('disabled') || e.hasAttribute('readonly') || e.getAttribute('aria-hidden') === 'true'
          || e.getAttribute('aria-disabled') === 'true' || (tag === 'input' && e.getAttribute('type') === 'hidden')) {
            return [];
        }
        const style = getComputedStyle(e) || {};
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            return [];
        }
        const events = window && typeof window.getEventListeners === 'function' ? window.getEventListeners(e) : [];
        const role = e.getAttribute('role');
        const clickableInputs = ['submit', 'checkbox', 'radio', 'color', 'file', 'image', 'reset'];
        function hasEvent(n) {
            return events[n]?.length || e.hasAttribute('on' + n);
        }
        const evts = [];
        if (hasEvent('keydown') || hasEvent('keyup') || hasEvent('keypress') || hasEvent('keydown') || hasEvent('input') || e.isContentEditable
          || (
            (tag === 'input' || tag === 'textarea' || role === 'searchbox' || role === 'input')
            ) && !clickableInputs.includes(e.getAttribute('type'))
          ) {
            evts.push('TYPE');
        }
        if (tag === 'a' || tag === 'button' || role === 'button' || role === 'checkbox' || hasEvent('click') || hasEvent('mousedown') || hasEvent('mouseup')
          || hasEvent('dblclick') || style.cursor === 'pointer' || (tag === 'input' && clickableInputs.includes(e.getAttribute('type')) )
          || e.hasAttribute('aria-haspopup') || tag === 'select' || role === 'select') {
            evts.push('CLICK');
        }
        return evts;
    }

    const results = {};
    function traverse(node, xpath) {
        if (node.nodeType === Node.ELEMENT_NODE) {
            const interactions = getInteractions(node);
            if (interactions.length > 0) {
                results[xpath] = interactions;
            }
        }
        const countByTag = {};
        for (let child = node.firstChild; child; child = child.nextSibling) {
            let tag = child.nodeName.toLowerCase();
            if (tag.includes(":")) continue; //namespace
            let isLocal = ['svg'].includes(tag);
            if (isLocal) {
                tag = `*[local-name() = '${tag}']`;
            }
            countByTag[tag] = (countByTag[tag] || 0) + 1;
            let childXpath = xpath + '/' + tag;
            if (countByTag[tag] > 1) {
                childXpath += '[' + countByTag[tag] + ']';
            }
            if (tag === 'iframe') {
                try {
                    traverse(child.contentWindow.document.body, childXpath + '/html/body');
                } catch (e) {
                    console.warn("iframe access blocked", child, e);
                }
            } else if (!isLocal) {
                traverse(child, childXpath);
            } 
        }
    }
    traverse(document.body, '/html/body');
    return results;
})();
"""

JS_GET_INTERACTIVES_IN_VIEWPORT = (
    """
const windowHeight = (window.innerHeight || document.documentElement.clientHeight);
const windowWidth = (window.innerWidth || document.documentElement.clientWidth);
return Object.fromEntries(Object.entries("""
    + js_wrap_function_call(JS_GET_INTERACTIVES)
    + """).filter(([xpath, evts]) => {
    const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    if (!element) return false;
    const rect = element.getBoundingClientRect();
    let iframe = element.ownerDocument.defaultView.frameElement;
    while (iframe) {
        const iframeRect = iframe.getBoundingClientRect();
        rect.top += iframeRect.top;
        rect.left += iframeRect.left;
        rect.bottom += iframeRect.top;
        rect.right += iframeRect.left;
        iframe = iframe.ownerDocument.defaultView.frameElement;
    }
    const elemCenter = {
        x: rect.left + element.offsetWidth / 2,
        y: rect.top + element.offsetHeight / 2
    };
    if (elemCenter.x < 0) return false;
    if (elemCenter.x > windowWidth) return false;
    if (elemCenter.y < 0) return false;
    if (elemCenter.y > windowHeight) return false;
    if (arguments?.[0] !== true) return true; // whenever to check for elements above
    let pointContainer = document.elementFromPoint(elemCenter.x, elemCenter.y);
    do {
        if (pointContainer === element) return true;
        if (pointContainer == null) return true;
    } while (pointContainer = pointContainer.parentNode);
    return false;
}));
"""
)

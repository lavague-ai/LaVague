from PIL import Image
import os
from pathlib import Path
import re
from typing import Any, Callable, Optional, Mapping, Dict, Set, List, Tuple, Union
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
import glob
from pathlib import Path


class InteractionType(Enum):
    CLICK = "click"
    HOVER = "hover"
    SCROLL = "scroll"
    TYPE = "type"


PossibleInteractionsByXpath = Dict[str, Set[InteractionType]]

r_get_xpaths_from_html = r'xpath=["\'](.*?)["\']'

class ScrollDirection(Enum):
    """Enum for the different scroll directions. Value is (x, y, dimension_index)"""

    LEFT = (-1, 0, 0)
    RIGHT = (1, 0, 0)
    UP = (0, -1, 1)
    DOWN = (0, 1, 1)

    def get_scroll_xy(
        self, dimension: List[float], scroll_factor: float = 0.75
    ) -> Tuple[int, int]:
        size = dimension[self.value[2]]
        return (
            round(self.value[0] * size * scroll_factor),
            round(self.value[1] * size * scroll_factor),
        )

    def get_page_script(self, scroll_factor: float = 0.75) -> str:
        return f"window.scrollBy({self.value[0] * scroll_factor} * window.innerWidth, {self.value[1] * scroll_factor} * window.innerHeight);"

    def get_script_element_is_scrollable(self) -> str:
        match self:
            case ScrollDirection.UP:
                return "return arguments[0].scrollTop > 0"
            case ScrollDirection.DOWN:
                return "return arguments[0].scrollTop + arguments[0].clientHeight + 1 < arguments[0].scrollHeight"
            case ScrollDirection.LEFT:
                return "return arguments[0].scrollLeft > 0"
            case ScrollDirection.RIGHT:
                return "return arguments[0].scrollLeft + arguments[0].clientWidth + 1 < arguments[0].scrollWidth"

    def get_script_page_is_scrollable(self) -> str:
        match self:
            case ScrollDirection.UP:
                return "return window.scrollY > 0"
            case ScrollDirection.DOWN:
                return "return window.innerHeight + window.scrollY + 1 < document.body.scrollHeight"
            case ScrollDirection.LEFT:
                return "return window.scrollX > 0"
            case ScrollDirection.RIGHT:
                return "return window.innerWidth + window.scrollX + 1 < document.body.scrollWidth"

    @classmethod
    def from_string(cls, name: str) -> "ScrollDirection":
        return cls[name.upper().strip()]


class BaseDriver(ABC):
    def __init__(self, url: Optional[str], init_function: Optional[Callable[[], Any]]):
        """Init the driver with the init funtion, and then go to the desired url"""
        self.init_function = (
            init_function if init_function is not None else self.default_init_code
        )
        self.driver = self.init_function()

        # Flag to check if the page has been previously scanned to avoid erasing screenshots from previous scan
        self.previously_scanned = False

        if url is not None:
            self.get(url)

    async def connect(self) -> None:
        """Connect to the driver"""
        pass

    @abstractmethod
    def default_init_code(self) -> Any:
        """Init the driver, with the imports, since it will be pasted to the beginning of the output"""
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

    @abstractmethod
    def resolve_xpath(self, xpath) -> "DOMNode":
        """
        Return the element for the corresponding xpath, the underlying driver may switch iframe if necessary
        """
        pass

    def save_screenshot(self, screenshot_folder: Path = Path("./screenshots")) -> str:
        """Save the screenshot data to a file and return the filename."""
        from datetime import datetime

        # Get current date and time
        now = datetime.now()
        new_screenshot_name  = now.strftime("%Y%m%d%H%M%S") + ".png"
        new_screenshot_full_path = screenshot_folder / new_screenshot_name
        # Get the screenshot
        screenshot = self.get_screenshot_as_png()

        if not screenshot_folder.exists():
            screenshot_folder.mkdir()

        with open(new_screenshot_full_path, "wb") as f:
            f.write(screenshot)
        return str(new_screenshot_full_path)

    def is_bottom_of_page(self) -> bool:
        return self.execute_script(
            "return (window.innerHeight + window.scrollY + 1) >= document.body.scrollHeight;"
        )

    @abstractmethod
    def get_possible_interactions(
        self,
        in_viewport=True,
        foreground_only=True,
        types: List[InteractionType] = [
            InteractionType.CLICK,
            InteractionType.TYPE,
            InteractionType.HOVER,
        ],
    ) -> PossibleInteractionsByXpath:
        """Get elements that can be interacted with as a dictionary mapped by xpath"""
        pass

    def get_in_viewport(self) -> List[str]:
        """Get xpath of elements in the viewport"""
        return []

    def check_visibility(self, xpath: str) -> bool:
        return True

    @abstractmethod
    def get_viewport_size(self) -> dict:
        """Return viewport size as {"width": int, "height": int}"""
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
    def execute_script(self, js_code: str, *args) -> Any:
        """Exec js script in DOM"""
        pass

    @abstractmethod
    def scroll(
        self,
        xpath_anchor: Optional[str],
        direction: ScrollDirection,
        scroll_factor=0.75,
    ):
        pass
    
    # TODO: Remove these methods as they are not used
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
        # We add labels to the scrollable elements
        i_scroll = self.get_possible_interactions(types=[InteractionType.SCROLL])
        scrollables_xpaths = list(i_scroll.keys())

        self.remove_highlight()
        self.highlight_nodes(scrollables_xpaths, label=True)

        # We take a screenshot and computes its hash to see if it already exists
        self.save_screenshot()

        # Delete the oldest screenshot if there are more than 2 to always keep 2 screenshots at most
        screenshots_dir = Path("screenshots")
        screenshot_files = glob.glob(str(screenshots_dir / "*.png"))
        
        # Delete the oldest screenshot if there are more than 2 to always keep 2 screenshots at most
        if len(screenshot_files) >= 3:
            # Sort files by modification time (oldest first)
            screenshot_files.sort(key=os.path.getmtime)
            # Delete the oldest file
            os.remove(screenshot_files[0])
        self.remove_highlight()

        url = self.get_url()
        html = self.get_html()
        obs = {
            "html": html,
            "screenshots_path": str(screenshots_dir),
            "url": url,
            "date": datetime.now().isoformat(),
            "tab_info": self.get_tabs(),
        }

        return obs

    def wait(self, duration):
        import time

        time.sleep(duration)

    def wait_for_idle(self):
        pass

    @abstractmethod
    def get_screenshot_as_png(self) -> bytes:
        pass

    @abstractmethod
    def get_shadow_roots(self) -> Dict[str, str]:
        pass

    def get_nodes(self, xpaths: List[str]) -> List["DOMNode"]:
        raise NotImplementedError("get_nodes not implemented")

    def get_nodes_from_html(self, html: str) -> List["DOMNode"]:
        return self.get_nodes(re.findall(r_get_xpaths_from_html, html))

    def highlight_node_from_xpath(
        self, xpath: str, color: str = "red", label=False
    ) -> Callable:
        return self.highlight_nodes([xpath], color, label)

    def highlight_nodes(
        self, xpaths: List[str], color: str = "red", label=False
    ) -> Callable:
        nodes = self.get_nodes(xpaths)
        for n in nodes:
            n.highlight(color)
        return self._add_highlighted_destructors(lambda: [n.clear() for n in nodes])

    def highlight_nodes_from_html(
        self, html: str, color: str = "blue", label=False
    ) -> Callable:
        return self.highlight_nodes(
            re.findall(r_get_xpaths_from_html, html), color, label
        )

    def remove_highlight(self):
        if hasattr(self, "_highlight_destructors"):
            for destructor in self._highlight_destructors:
                destructor()
            delattr(self, "_highlight_destructors")

    def _add_highlighted_destructors(
        self, destructors: Union[List[Callable], Callable]
    ) -> Callable:
        if not hasattr(self, "_highlight_destructors"):
            self._highlight_destructors = []
        if isinstance(destructors, Callable):
            self._highlight_destructors.append(destructors)
            return destructors

        self._highlight_destructors.extend(destructors)
        return lambda: [d() for d in destructors]

    def highlight_interactive_nodes(
        self,
        *with_interactions: tuple[InteractionType],
        color: str = "red",
        in_viewport=True,
        foreground_only=True,
        label=False,
    ):
        if with_interactions is None or len(with_interactions) == 0:
            return self.highlight_nodes(
                list(
                    self.get_possible_interactions(
                        in_viewport=in_viewport, foreground_only=foreground_only
                    ).keys()
                ),
                color,
                label,
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
            label,
        )


class DOMNode(ABC):
    @property
    @abstractmethod
    def element(self) -> Any:
        pass

    @property
    @abstractmethod
    def value(self) -> Any:
        pass

    @abstractmethod
    def highlight(self, color: str = "red", bounding_box=True):
        pass

    @abstractmethod
    def clear(self):
        return self

    @abstractmethod
    def take_screenshot(self) -> Image.Image:
        pass

    @abstractmethod
    def get_html(self) -> str:
        pass

    def __str__(self) -> str:
        return self.get_html()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass




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
                if (!this.eventListenerList[a].length) {
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
const windowHeight = (window.innerHeight || document.documentElement.clientHeight);
const windowWidth = (window.innerWidth || document.documentElement.clientWidth);

return (function(inViewport, foregroundOnly, nonInteractives, filterTypes) {
    function getInteractions(e) {
        const tag = e.tagName.toLowerCase();
        if (!e.checkVisibility() || (e.hasAttribute('disabled') && !nonInteractives) || e.hasAttribute('readonly')
          || (tag === 'input' && e.getAttribute('type') === 'hidden') || tag === 'body') {
            return [];
        }
        const rect = e.getBoundingClientRect();
        if (rect.width + rect.height < 5) {
            return [];
        }
        const style = getComputedStyle(e) || {};
        if (style.display === 'none' || style.visibility === 'hidden') {
            return [];
        }
        const events = window && typeof window.getEventListeners === 'function' ? window.getEventListeners(e) : [];
        const role = e.getAttribute('role');
        const clickableInputs = ['submit', 'checkbox', 'radio', 'color', 'file', 'image', 'reset'];
        function hasEvent(n) {
            return events[n]?.length || e.hasAttribute('on' + n);
        }
        let evts = [];
        if (hasEvent('keydown') || hasEvent('keyup') || hasEvent('keypress') || hasEvent('keydown') || hasEvent('input') || e.isContentEditable
          || (
            (tag === 'input' || tag === 'textarea' || role === 'searchbox' || role === 'input')
            ) && !clickableInputs.includes(e.getAttribute('type'))
          ) {
            evts.push('TYPE');
        }
        if (['a', 'button', 'select'].includes(tag) || ['button', 'checkbox', 'select'].includes(role)
            || hasEvent('click') || hasEvent('mousedown') || hasEvent('mouseup') || hasEvent('dblclick')
            || style.cursor === 'pointer'
            || e.hasAttribute('aria-haspopup')
            || (tag === 'input' && clickableInputs.includes(e.getAttribute('type')))
            || (tag === 'label' && document.getElementById(e.getAttribute('for')))
        ) {
            evts.push('CLICK');
        }
        if (
            (hasEvent('scroll') || hasEvent('wheel') || style.overflow === 'auto' || style.overflow === 'scroll' || style.overflowY === 'auto' || style.overflowY === 'scroll')
            && (e.scrollHeight > e.clientHeight || e.scrollWidth > e.clientWidth)) {
            evts.push('SCROLL');
        }
        if (filterTypes && evts.length) {
            evts = evts.filter(t => filterTypes.includes(t));
        }
        if (nonInteractives && evts.length === 0) {
            evts.push('NONE');
        }

        if (inViewport) {
            let rect = e.getBoundingClientRect();
            let iframe = e.ownerDocument.defaultView.frameElement;
            while (iframe) {
                const iframeRect = iframe.getBoundingClientRect();
                rect = {
                    top: rect.top + iframeRect.top,
                    left: rect.left + iframeRect.left,
                    bottom: rect.bottom + iframeRect.bottom,
                    right: rect.right + iframeRect.right,
                    width: rect.width,
                    height: rect.height
                }
                iframe = iframe.ownerDocument.defaultView.frameElement;
            }
            const elemCenter = {
                x: Math.round(rect.left + rect.width / 2),
                y: Math.round(rect.top + rect.height / 2)
            };
            if (elemCenter.x < 0) return [];
            if (elemCenter.x > windowWidth) return [];
            if (elemCenter.y < 0) return [];
            if (elemCenter.y > windowHeight) return [];
            if (!foregroundOnly) return evts; // whenever to check for elements above
            let pointContainer = document.elementFromPoint(elemCenter.x, elemCenter.y);
            iframe = e.ownerDocument.defaultView.frameElement;
            while (iframe) {
                const iframeRect = iframe.getBoundingClientRect();
                pointContainer = iframe.contentDocument.elementFromPoint(
                    elemCenter.x - iframeRect.left,
                    elemCenter.y - iframeRect.top
                );
                iframe = iframe.ownerDocument.defaultView.frameElement;
            }
            do {
                if (pointContainer === e) return evts;
                if (pointContainer == null) return evts;
            } while (pointContainer = pointContainer.parentNode);
            return [];
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
                if (child.shadowRoot) {
                    traverse(child.shadowRoot, childXpath + '/');
                }
            } 
        }
    }
    traverse(document.body, '/html/body');
    return results;
})(arguments?.[0], arguments?.[1], arguments?.[2], arguments?.[3]);
"""

JS_WAIT_DOM_IDLE = """
return new Promise(resolve => {
    const timeout = arguments[0] || 10000;
    const stabilityThreshold = arguments[1] || 100;

    let mutationObserver;
    let timeoutId = null;

    const waitForIdle = () => {
        if (timeoutId) clearTimeout(timeoutId);
        timeoutId = setTimeout(() => resolve(true), stabilityThreshold);
    };
    mutationObserver = new MutationObserver(waitForIdle);
    mutationObserver.observe(document.body, {
        childList: true,
        attributes: true,
        subtree: true,
    });
    waitForIdle();

    setTimeout(() => {
        resolve(false);
        mutationObserver.disconnect();
        mutationObserver = null;
        if (timeoutId) {
            clearTimeout(timeoutId);
            timeoutId = null;
        }
    }, timeout);
});
"""

JS_GET_SCROLLABLE_PARENT = """
let element = arguments[0];
while (element) {
    const style = window.getComputedStyle(element);

    // Check if the element is scrollable
    if (style.overflow === 'auto' || style.overflow === 'scroll' || 
        style.overflowX === 'auto' || style.overflowX === 'scroll' || 
        style.overflowY === 'auto' || style.overflowY === 'scroll') {
        
        // Check if the element has a scrollable area
        if (element.scrollHeight > element.clientHeight || 
            element.scrollWidth > element.clientWidth) {
            return element;
        }
    }
    element = element.parentElement;
}
return null;
"""

JS_GET_SHADOW_ROOTS = """
const results = {};
function traverse(node, xpath) {
    if (node.shadowRoot) {
        results[xpath] = node.shadowRoot.getHTML();
    }
    const countByTag = {};
    for (let child = node.firstChild; child; child = child.nextSibling) {
        let tag = child.nodeName.toLowerCase();
        countByTag[tag] = (countByTag[tag] || 0) + 1;
        let childXpath = xpath + '/' + tag;
        if (countByTag[tag] > 1) {
            childXpath += '[' + countByTag[tag] + ']';
        }
        if (child.shadowRoot) {
            traverse(child.shadowRoot, childXpath + '/');
        }
        if (tag === 'iframe') {
            try {
                traverse(child.contentWindow.document.body, childXpath + '/html/body');
            } catch (e) {
                console.warn("iframe access blocked", child, e);
            }
        } else {
            traverse(child, childXpath);
        }
    }
}
traverse(document.body, '/html/body');
return results;
"""

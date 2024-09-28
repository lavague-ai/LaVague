from PIL import Image
import re
from typing import Any, Callable, Optional, Mapping, Dict, Set, List, Tuple, Union
from abc import ABC, abstractmethod
from enum import Enum


class InteractionType(Enum):
    CLICK = "click"
    HOVER = "hover"
    SCROLL = "scroll"
    TYPE = "type"


PossibleInteractionsByXpath = Dict[str, Set[InteractionType]]

r_get_xpaths_from_html = r'xpath=["\'](.*?)["\']'


class BaseDriver(ABC):
    @abstractmethod
    def destroy(self) -> None:
        """Cleanly destroy the underlying driver"""
        pass

    @abstractmethod
    def get_url(self) -> Optional[str]:
        """Get the url of the current page"""
        pass

    @abstractmethod
    def get(self, url: str) -> None:
        """Navigate to the url"""
        pass

    @abstractmethod
    def back(self) -> None:
        """Navigate back"""
        pass

    @abstractmethod
    def get_html(self) -> str:
        """
        Returns the HTML of the current page.
        If clean is True, We remove unnecessary tags and attributes from the HTML.
        Clean HTMLs are easier to process for the LLM.
        """
        pass

    @abstractmethod
    def get_tabs(self) -> str:
        """Return description of the tabs opened with the current tab being focused.

        Example of output:
        Tabs opened:
        0 - Overview - OpenAI API
        1 - [CURRENT] Nos destinations Train - SNCF Connect
        """
        return "Tabs opened:\n 0 - [CURRENT] tab"

    @abstractmethod
    def switch_tab(self, tab_id: int) -> None:
        """Switch to the tab with the given id"""
        pass

    @abstractmethod
    def resolve_xpath(self, xpath) -> "DOMNode":
        """
        Return the element for the corresponding xpath, the underlying driver may switch iframe if necessary
        """
        pass

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
    def scroll_up(self):
        pass

    @abstractmethod
    def scroll_down(self):
        pass

    @abstractmethod
    def get_capability(self) -> str:
        """Prompt to explain the llm which style of code he should output and which variables and imports he should expect"""
        pass

    @abstractmethod
    def wait_for_idle(self):
        pass

    @abstractmethod
    def get_screenshot_as_png(self) -> bytes:
        pass

    @abstractmethod
    def get_shadow_roots(self) -> Dict[str, str]:
        return {}

    @abstractmethod
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

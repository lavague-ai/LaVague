import re
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Callable, Dict, Generic, List, Optional, TypeVar, Union

from lavague.sdk.action.navigation import NavigationCommand, NavigationOutput
from lavague.sdk.base_driver.interaction import (
    InteractionType,
    PossibleInteractionsByXpath,
    ScrollDirection,
)
from lavague.sdk.base_driver.node import DOMNode
from pydantic import BaseModel


class DriverObservation(BaseModel):
    html: str
    screenshot: bytes
    url: str
    date: str
    tab_info: str


T = TypeVar("T", bound=DOMNode, covariant=True)


class BaseDriver(ABC, Generic[T]):
    @abstractmethod
    def init(self) -> None:
        """Init the underlying driver"""
        pass

    def execute(self, action: NavigationOutput) -> None:
        """Execute an action"""
        with self.resolve_xpath(action.xpath) as node:
            match action.navigation_command:
                case NavigationCommand.CLICK:
                    node.click()

                case NavigationCommand.SET_VALUE:
                    node.set_value(action.value or "")

                case NavigationCommand.SET_VALUE_AND_ENTER:
                    node.set_value((action.value or "") + "\ue007")

                case NavigationCommand.TYPE_KEY:
                    self.type_key(action.value or "")

                case NavigationCommand.HOVER:
                    node.hover()

                case NavigationCommand.BACK:
                    self.back()

                case NavigationCommand.PASS:
                    pass

                case NavigationCommand.SCROLL:
                    direction = ScrollDirection.from_string(action.value or "DOWN")
                    self.scroll(action.xpath, direction)

                case NavigationCommand.SWITCH_TAB:
                    self.switch_tab(int(action.value or "0"))

                case _:
                    raise NotImplementedError(
                        f"Action {action.navigation_command} not implemented"
                    )

    @abstractmethod
    def destroy(self) -> None:
        """Cleanly destroy the underlying driver"""
        pass

    @abstractmethod
    def resize_driver(self, width: int, height: int):
        """Resize the viewport to a targeted height and width"""

    @abstractmethod
    def get_url(self) -> str:
        """Get the url of the current page, raise NoPageException if no page is loaded"""
        pass

    @abstractmethod
    def get(self, url: str) -> None:
        """Navigate to the url"""
        pass

    @abstractmethod
    def back(self) -> None:
        """Navigate back, raise CannotBackException if history root is reached"""
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
        pass

    @abstractmethod
    def switch_tab(self, tab_id: int) -> None:
        """Switch to the tab with the given id"""
        pass

    @abstractmethod
    def type_key(self, key: str) -> None:
        """Type a key"""
        pass

    @abstractmethod
    def resolve_xpath(self, xpath: str) -> T:
        """
        Return the element for the corresponding xpath, the underlying driver may switch iframe if necessary
        """
        pass

    @abstractmethod
    def get_viewport_size(self) -> dict:
        """Return viewport size as {"width": int, "height": int}"""
        pass

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

    @abstractmethod
    def scroll(
        self,
        xpath_anchor: Optional[str] = "/html/body",
        direction: ScrollDirection = ScrollDirection.DOWN,
        scroll_factor=0.75,
    ):
        pass

    @abstractmethod
    def scroll_into_view(self, xpath: str):
        pass

    @abstractmethod
    def wait_for_idle(self):
        pass

    @abstractmethod
    def get_capability(self) -> str:
        """Prompt to explain the llm which style of code he should output and which variables and imports he should expect"""
        pass

    @abstractmethod
    def get_screenshot_as_png(self) -> bytes:
        pass

    @abstractmethod
    def get_shadow_roots(self) -> Dict[str, str]:
        """Return a dictionary of shadow roots HTML by xpath"""
        pass

    @abstractmethod
    def get_nodes(self, xpaths: List[str]) -> List[T]:
        pass

    @abstractmethod
    def highlight_nodes(
        self, xpaths: List[str], color: str = "red", label=False
    ) -> Callable:
        pass

    @abstractmethod
    def switch_frame(self, xpath: str) -> None:
        """Switch to the frame with the given xpath, use with care as it changes the state of the driver"""
        pass

    @abstractmethod
    def switch_parent_frame(self) -> None:
        """Switch to the parent frame, use with care as it changes the state of the driver"""
        pass

    @contextmanager
    def nodes_highlighter(self, nodes: List[str], color: str = "red", label=False):
        """Highlight nodes for a context manager"""
        remove_highlight = self.highlight_nodes(nodes, color, label)
        yield
        remove_highlight()

    def get_obs(self) -> DriverObservation:
        """Get the current observation of the driver"""

        # We add labels to the scrollable elements
        scrollables = self.get_scroll_containers()
        with self.nodes_highlighter(scrollables, label=True):
            screenshot = self.get_screenshot_as_png()

        url = self.get_url()
        html = self.get_html()
        tab_info = self.get_tabs()

        return DriverObservation(
            html=html,
            screenshot=screenshot,
            url=url,
            date=datetime.now().isoformat(),
            tab_info=tab_info,
        )

    def get_in_viewport(self) -> List[str]:
        """Get xpath of elements in the viewport"""
        interactions = self.get_possible_interactions(in_viewport=True, types=[])
        return list(interactions.keys())

    def get_scroll_containers(self) -> List[str]:
        """Get xpath of elements in the viewport"""
        interactions = self.get_possible_interactions(types=[InteractionType.SCROLL])
        return list(interactions.keys())

    def get_nodes_from_html(self, html: str) -> List[T]:
        return self.get_nodes(re.findall(r"xpath=[\"'](.*?)[\"']", html))

    def highlight_node_from_xpath(
        self, xpath: str, color: str = "red", label=False
    ) -> Callable:
        return self.highlight_nodes([xpath], color, label)

    def highlight_nodes_from_html(
        self, html: str, color: str = "blue", label=False
    ) -> Callable:
        return self.highlight_nodes(
            re.findall(r"xpath=[\"'](.*?)[\"']", html), color, label
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

    def __enter__(self):
        self.init()
        self.driver_ready = True
        return self

    def __exit__(self, *_):
        self.destroy()
        self.driver_ready = False

    def __del__(self):
        if getattr(self, "driver_ready", False):
            self.__exit__()

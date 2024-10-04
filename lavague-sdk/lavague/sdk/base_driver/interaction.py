from typing import Dict, Set, List, Tuple
from enum import Enum


class InteractionType(Enum):
    CLICK = "click"
    HOVER = "hover"
    SCROLL = "scroll"
    TYPE = "type"


PossibleInteractionsByXpath = Dict[str, Set[InteractionType]]


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

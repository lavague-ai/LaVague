from enum import Enum
from pydantic import BaseModel
from lavague.sdk.action import Action
from typing import Optional


class NavigationCommand(str, Enum):
    CLICK = "click"
    HOVER = "hover"
    SET_VALUE = "set_value"
    SET_VALUE_AND_ENTER = "set_value_and_enter"
    TYPE_KEY = "type_key"
    SCROLL = "scroll"


class NavigationOutput(BaseModel):
    navigation_command: NavigationCommand
    xpath: str
    value: Optional[str]


class WebNavigationAction(Action[NavigationOutput]):
    pass

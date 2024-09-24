from enum import Enum
from pydantic import BaseModel
from lavague.action import Action
from typing import Optional

class NavigationCommand(Enum):
    CLICK = "click"
    HOVER = "hover"
    SET_VALUE = "set_value"
    TYPE_KEY = "type_key"
    SCROLL = "scroll"
    
class NavigationOutput(BaseModel):
    navigation_command: NavigationCommand
    xpath: str
    value: Optional[str]

class WebNavigationAction(Action[NavigationOutput]):
    pass
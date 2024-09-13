from lavague.core.action import Action
from enum import Enum
from typing import Any, ClassVar, Dict, Type, Optional
from pydantic import BaseModel


class NavigationActionType(Enum):
    """Types of navigation actions."""

    CLICK = "click"
    SET_VALUE = "setValue"
    SET_VALUE_AND_ENTER = "setValueAndEnter"
    DROPDOWN_SELECT = "dropdownSelect"
    HOVER = "hover"


class NavigationActionArgs(BaseModel):
    """Arguments for navigation action."""

    xpath: str
    name: NavigationActionType
    value: Optional[str] = None


class NavigationAction(Action[NavigationActionArgs]):
    """Navigation action performed by the agent."""

    subtypes: ClassVar[Dict[str, Type["NavigationAction"]]] = {}

    args: NavigationActionArgs

    @classmethod
    def parse(cls, action_dict: Any) -> "NavigationAction":
        subtype = action_dict.get("args", {}).get("name")
        target_type = cls.subtypes.get(subtype, NavigationAction)
        return target_type(**action_dict)

    @classmethod
    def register_subtype(cls, subtype: str, action: Type["NavigationAction"]):
        cls.subtypes[subtype] = action
        return cls


def register_navigation(name: str):
    return lambda cls: NavigationAction.register_subtype(name, cls)


class NavigationWithValueActionArgs(NavigationActionArgs):
    """Arguments for navigation action with a value."""

    value: str


class NavigationWithValueAction(NavigationAction):
    """Navigation action performed by the agent with a value."""

    args: NavigationWithValueActionArgs


@register_navigation(NavigationActionType.CLICK.value)
class ClickAction(NavigationAction):
    pass


@register_navigation(NavigationActionType.HOVER.value)
class HoverAction(NavigationAction):
    pass


@register_navigation(NavigationActionType.SET_VALUE.value)
class SetValueAction(NavigationWithValueAction):
    pass


@register_navigation(NavigationActionType.SET_VALUE_AND_ENTER.value)
class SetValueAndEnterAction(SetValueAction):
    pass


@register_navigation(NavigationActionType.DROPDOWN_SELECT.value)
class DropdownSelectAction(NavigationWithValueAction):
    pass

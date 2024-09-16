from lavague.core.action import Action, UnhandledTypeException
from enum import Enum
from typing import ClassVar, Dict, Type, Optional


class NavigationActionType(Enum):
    """Types of navigation actions."""

    CLICK = "click"
    SET_VALUE = "setValue"
    SET_VALUE_AND_ENTER = "setValueAndEnter"
    DROPDOWN_SELECT = "dropdownSelect"
    HOVER = "hover"
    SCROLL_DOWN = "scroll_down"
    SCROLL_UP = "scroll_up"
    BACK = "back"


class NavigationAction(Action):
    """Navigation action performed by the agent."""

    subtypes: ClassVar[Dict[str, Type["NavigationAction"]]] = {}

    xpath: str
    action: NavigationActionType
    value: Optional[str] = None

    @classmethod
    def parse(cls, action_dict: Dict) -> "NavigationAction":
        action_name = action_dict.get("action")
        try:
            NavigationActionType(action_name)
        except ValueError:
            raise UnhandledTypeException(f"Unhandled action type: {action_name}")

        target_type = cls.subtypes.get(action_name, NavigationAction)
        return target_type(**action_dict)

    @classmethod
    def register_subtype(cls, subtype: str, action: Type["NavigationAction"]):
        cls.subtypes[subtype] = action
        return cls


def register_navigation(name: str):
    return lambda cls: NavigationAction.register_subtype(name, cls)


class NavigationWithValueAction(NavigationAction):
    """Navigation action performed by the agent with a value."""

    value: str


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


@register_navigation(NavigationActionType.SCROLL_DOWN.value)
class ScrollDownAction(NavigationAction):
    pass


@register_navigation(NavigationActionType.SCROLL_UP.value)
class ScrollUpAction(NavigationAction):
    pass


@register_navigation(NavigationActionType.BACK.value)
class BackAction(NavigationAction):
    pass
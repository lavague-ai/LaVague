from lavague.action import Action
from typing import ClassVar, Dict, Type, Optional, TypeVar

T = TypeVar("T", bound="NavigationAction")


class NavigationAction(Action):
    """Navigation action performed by the agent."""

    subtypes: ClassVar[Dict[str, Type["NavigationAction"]]] = {}

    xpath: str
    value: Optional[str] = None

    @classmethod
    def parse(cls, action_dict: Dict) -> "NavigationAction":
        action_name = action_dict.get("action", "")
        target_type = cls.subtypes.get(action_name, NavigationAction)
        return target_type(**action_dict)

    @classmethod
    def register_subtype(cls, subtype: str, action: Type[T]):
        cls.subtypes[subtype] = action
        return cls


def register_navigation(name: str):
    def wrapper(cls: Type[T]) -> Type[T]:
        NavigationAction.register_subtype(name, cls)
        return cls

    return wrapper


class NavigationWithValueAction(NavigationAction):
    """Navigation action performed by the agent with a value."""

    value: str


@register_navigation("click")
class ClickAction(NavigationAction):
    pass


@register_navigation("hover")
class HoverAction(NavigationAction):
    pass


@register_navigation("setValue")
class SetValueAction(NavigationWithValueAction):
    pass


@register_navigation("setValueAndEnter")
class SetValueAndEnterAction(SetValueAction):
    pass


@register_navigation("dropdownSelect")
class DropdownSelectAction(NavigationWithValueAction):
    pass


@register_navigation("scroll_down")
class ScrollDownAction(NavigationAction):
    pass


@register_navigation("scroll_up")
class ScrollUpAction(NavigationAction):
    pass


@register_navigation("back")
class BackAction(NavigationAction):
    pass


@register_navigation("switch_tab")
class SwitchTabAction(NavigationAction):
    pass

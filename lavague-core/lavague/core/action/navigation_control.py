from lavague.core.action import Action
from enum import Enum
from pydantic import BaseModel
from typing import Any, ClassVar, Dict, Type


class ControlsActionType(Enum):
    """Types of controls actions."""

    SCROLL_DOWN = "scroll_down"
    SCROLL_UP = "scroll_up"
    BACK = "back"
    SCAN = "scan"


class ControlsActionArgs(BaseModel):
    """Arguments for controls action."""

    name: ControlsActionType


class ControlsAction(Action[ControlsActionArgs]):
    """Controls action performed by the agent."""

    subtypes: ClassVar[Dict[str, Type["ControlsActionArgs"]]] = {}

    args: ControlsActionArgs

    @classmethod
    def parse(cls, action_dict: Any) -> "ControlsAction":
        subtype = action_dict.get("args", {}).get("name")
        target_type = cls.subtypes.get(subtype, ControlsAction)
        return target_type(**action_dict)

    @classmethod
    def register_subtype(cls, subtype: str, action: Type["ControlsAction"]):
        cls.subtypes[subtype] = action
        return cls


def register_control(name: str):
    return lambda cls: ControlsAction.register_subtype(name, cls)


@register_control(ControlsActionType.SCROLL_UP.value)
class ScrollUpAction(ControlsAction):
    pass


@register_control(ControlsActionType.SCROLL_DOWN.value)
class ScrollDownAction(ControlsAction):
    pass


@register_control(ControlsActionType.BACK.value)
class BackAction(ControlsAction):
    pass


@register_control(ControlsActionType.SCAN.value)
class ScanAction(ControlsAction):
    pass

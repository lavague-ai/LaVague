from typing import Dict, Type, Optional, Callable, TypeVar, Self
from pydantic import BaseModel, validate_call
from enum import Enum


class ActionStatus(Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class Action(BaseModel):
    """Action performed by the agent."""

    engine: str
    action: str
    status: ActionStatus

    @classmethod
    def parse(cls, action_dict: Dict) -> "Action":
        return cls(**action_dict)

    @classmethod
    def add_translator(cls, name: str, translator: "ActionTranslator[Self]"):
        setattr(cls, name, translator)


class ActionParser(BaseModel):
    engine_action_builders: Dict[str, Type[Action]]

    def __init__(self):
        super().__init__(engine_action_builders={})

    @validate_call
    def register(self, engine: str, action: Type[Action]):
        self.engine_action_builders[engine] = action

    def unregister(self, engine: str):
        if engine in self.engine_action_builders:
            del self.engine_action_builders[engine]

    def parse(self, action_dict: Dict) -> Action:
        engine = action_dict.get("engine", "")
        target_type: Type[Action] = self.engine_action_builders.get(engine, Action)
        try:
            return target_type.parse(action_dict)
        except UnhandledTypeException:
            return Action.parse(action_dict)


class UnhandledTypeException(Exception):
    pass


T = TypeVar("T", bound=Action)


ActionTranslator = Callable[[T], Optional[str]]


DEFAULT_PARSER = ActionParser()

from typing import Dict, List, Type, Generic, TypeVar
from pydantic import BaseModel, validate_call, Field, SerializeAsAny
from enum import Enum
from uuid import uuid4


class ActionStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(str, Enum):
    NAVIGATION = "web_navigation"
    EXTRACTION = "web_extraction"


T = TypeVar("T")


class Action(BaseModel, Generic[T]):
    """Action performed by the agent."""

    step_id: str = Field(default_factory=lambda: str(uuid4()))
    action_type: ActionType
    action_output: List[SerializeAsAny[T]]
    url: str
    status: ActionStatus
    instruction: str

    @classmethod
    def parse(cls, action_dict: Dict) -> "Action":
        return cls(**action_dict)


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
        engine = action_dict.get("action_type", "")
        target_type: Type[Action] = self.engine_action_builders.get(engine, Action)
        try:
            return target_type.parse(action_dict)
        except UnhandledTypeException:
            return Action.parse(action_dict)


class UnhandledTypeException(Exception):
    pass


DEFAULT_PARSER = ActionParser()

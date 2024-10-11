from enum import Enum
from typing import Any, Dict, List, Tuple, Optional
from pydantic import BaseModel, SerializeAsAny
from lavague.sdk.action import Action, ActionParser, Instruction
from lavague.sdk.action.base import DEFAULT_PARSER
from pydantic import model_validator
from pydantic_core import from_json


class RunStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class RunMode(str, Enum):
    LIVE = "live"
    STEP_BY_STEP = "step_by_step"
    INACTIVE = "inactive"


class TrajectoryData(BaseModel):
    """Trajectory of web interactions towards an objective."""

    run_id: str
    start_url: str
    objective: str
    viewport_size: Tuple[int, int]
    status: RunStatus
    run_mode: RunMode = RunMode.INACTIVE
    actions: List[SerializeAsAny[Action]]
    error_msg: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def deserialize_actions(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "actions" in values:
            actions = values["actions"]
            deserialized_actions = []
            for action_data in actions:
                if isinstance(action_data, Action):
                    deserialized_actions.append(action_data)
                    continue
                action_type = action_data.get("action_type")
                if action_type:
                    action_class = DEFAULT_PARSER.engine_action_builders.get(
                        action_type, Action
                    )
                    deserialized_action = action_class.parse(action_data)
                    deserialized_actions.append(deserialized_action)
                else:
                    deserialized_actions.append(Action.parse(action_data))
            values["actions"] = deserialized_actions
        return values

    def write_to_file(self, file_path: str):
        json_model = self.model_dump_json(indent=2)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(json_model)


class ActionWrapper(BaseModel):
    action: Optional[Action]

    @classmethod
    def from_data(
        cls,
        data: str | bytes | bytearray,
        parser: ActionParser = DEFAULT_PARSER,
    ):
        obj = from_json(data)
        return cls.from_dict(obj, parser)

    @classmethod
    def from_dict(
        cls,
        data: Dict,
        parser: ActionParser = DEFAULT_PARSER,
    ):
        action = data.get("action")
        action = parser.parse(action) if action else None
        return cls.model_validate({**data, "action": action})

    @model_validator(mode="before")
    @classmethod
    def deserialize_action(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "action" in values:
            action_data = values["action"]
            if not isinstance(action_data, Action) and "action_type" in action_data:
                action_class = DEFAULT_PARSER.engine_action_builders.get(
                    action_data["action_type"], Action
                )
                deserialized_action = action_class.parse(action_data)
                values["action"] = deserialized_action
        return values


class StepCompletion(ActionWrapper):
    run_status: RunStatus
    run_mode: RunMode


class StepKnowledge(ActionWrapper):
    instruction: Instruction

from enum import Enum
from typing import Any, Dict, List, Tuple, Optional
from pydantic import BaseModel, SerializeAsAny
from lavague.sdk.action import Action
from lavague.sdk.action.base import DEFAULT_PARSER
from pydantic import model_validator

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

    @model_validator(mode='before')
    @classmethod
    def deserialize_actions(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if 'actions' in values:
            actions = values['actions']
            deserialized_actions = []
            for action_data in actions:
                action_type = action_data.get('action_type')
                if action_type:
                    action_class = DEFAULT_PARSER.engine_action_builders.get(action_type, Action)
                    deserialized_action = action_class.parse(action_data)
                    deserialized_actions.append(deserialized_action)
                else:
                    deserialized_actions.append(Action.parse(action_data))
            values['actions'] = deserialized_actions
        return values

    def write_to_file(self, file_path: str):
        json_model = self.model_dump_json(indent=2)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(json_model)

class StepCompletion(BaseModel):
    run_status: RunStatus
    action: Optional[Action]

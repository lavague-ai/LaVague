from typing import Optional, List, Tuple
from pydantic import BaseModel, SerializeAsAny
from lavague.sdk.action import Action, WebExtractionAction, WebNavigationAction
from enum import Enum
from pydantic_core import from_json
from lavague.sdk.action import ActionParser, DEFAULT_PARSER


class TrajectoryStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Trajectory(BaseModel):
    """Observable trajectory of web interactions towards an objective."""

    run_id: str
    start_url: str
    viewport_size: Tuple[int, int]
    objective: str
    status: TrajectoryStatus
    actions: List[SerializeAsAny[Action]]

    def write_to_file(self, file_path: str):
        json_model = self.model_dump_json(indent=2)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(json_model)

    @classmethod
    def from_data(
        cls, data: str | bytes | bytearray, parser: ActionParser = DEFAULT_PARSER
    ):
        obj = from_json(data)
        obj["actions"] = [parser.parse(action) for action in obj.get("actions", [])]
        return cls.model_validate(obj)

    @classmethod
    # TODO: This code is a fix from this code
    # def from_dict(cls, data: dict, parser: ActionParser = DEFAULT_PARSER):
    #     data["actions"] = [parser.parse(action) for action in data.get("actions", [])]
    #     return cls.model_validate(data)
    def from_dict(cls, data: dict):
        actions = []
        for action in data.get("actions", []):
            action_type = action.get("action_type")
            if action_type == "web_navigation":
                actions.append(WebNavigationAction.parse(action))
            elif action_type == "web_extraction":
                actions.append(WebExtractionAction.parse(action))
            else:
                # Fallback to generic Action if type is unknown
                actions.append(Action.parse(action))
        data["actions"] = actions
        return cls(**data)

    @classmethod
    def from_file(
        cls, file_path: str, parser: ActionParser = DEFAULT_PARSER, encoding="utf-8"
    ):
        with open(file_path, "r", encoding=encoding) as file:
            content = file.read()
            return cls.from_data(content, parser)

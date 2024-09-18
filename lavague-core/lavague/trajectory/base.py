from typing import Optional, List
from pydantic import BaseModel, SerializeAsAny
from lavague.action import Action
from enum import Enum
from pydantic_core import from_json
from lavague.action import ActionParser, DEFAULT_PARSER


class TrajectoryStatus(Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class Trajectory(BaseModel):
    """Observable trajectory of web interactions towards an objective."""

    url: str
    objective: str
    status: TrajectoryStatus
    output: Optional[str]
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
    def from_file(
        cls, file_path: str, parser: ActionParser = DEFAULT_PARSER, encoding="utf-8"
    ):
        with open(file_path, "r", encoding=encoding) as file:
            content = file.read()
            return cls.from_data(content, parser)
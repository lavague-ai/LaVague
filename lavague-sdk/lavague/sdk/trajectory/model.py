from enum import Enum
from typing import List, Tuple, Optional
from pydantic import BaseModel, SerializeAsAny
from lavague.sdk.action import Action


class RunStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class TrajectoryData(BaseModel):
    """Trajectory of web interactions towards an objective."""

    run_id: str
    start_url: str
    objective: str
    viewport_size: Tuple[int, int]
    status: RunStatus
    actions: List[SerializeAsAny[Action]]
    error_msg: Optional[str] = None

    def write_to_file(self, file_path: str):
        json_model = self.model_dump_json(indent=2)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(json_model)


class StepCompletion(BaseModel):
    run_status: RunStatus
    action: Optional[Action]

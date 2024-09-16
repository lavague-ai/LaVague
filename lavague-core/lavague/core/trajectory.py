from typing import Optional, Generator, List
from pydantic import BaseModel
from lavague.core.action.base import Action
from enum import Enum


class TrajectoryStatus(Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class Trajectory(BaseModel):
    """Observable trajectory of web interactions towards an objective."""

    url: str
    objective: str
    actions: List[Action]
    status: TrajectoryStatus
    final_html: Optional[str]
    output: Optional[str]

    def __iter__(self) -> Generator[Action, None, None]:
        yield from self.actions

from typing import Optional, Generator, List
from pydantic import BaseModel
from lavague.core.action.base import Action


class Trajectory(BaseModel):
    """Observable trajectory of web interactions towards an objective."""

    url: str
    objective: str
    actions: List[Action]
    success: bool
    final_html: Optional[str]
    output: Optional[str]

    def __iter__(self) -> Generator[Action, None, None]:
        yield from self.actions

from abc import ABC, abstractmethod
from typing import Any, Optional
from lavague.core.display import Display
from lavague.core.logger import Loggable
from dataclasses import dataclass


@dataclass
class ActionResult:
    """Represent the result of executing an instruction"""

    instruction: str
    code: str
    success: bool
    output: Any
    total_estimated_tokens: Optional[int] = 0
    total_estimated_cost: Optional[float] = 0


class BaseEngine(ABC, Loggable, Display):
    @abstractmethod
    def execute_instruction(self, instruction: str) -> ActionResult:
        pass

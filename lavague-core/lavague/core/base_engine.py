from abc import ABC, abstractmethod
from typing import Any, Tuple
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


class BaseEngine(ABC, Loggable, Display):
    @abstractmethod
    def execute_instruction(self, instruction: str) -> ActionResult:
        pass

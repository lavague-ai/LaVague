from abc import ABC, abstractmethod
from typing import Any, Tuple
from lavague.core.logger import Loggable

class BaseEngine(ABC, Loggable):
    @abstractmethod
    def execute_instruction(self, instruction: str) -> Tuple[bool, Any]:
        pass
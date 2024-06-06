from abc import ABC, abstractmethod
from typing import Any, Tuple
from lavague.core.display import Display
from lavague.core.logger import Loggable


class BaseEngine(ABC, Loggable, Display):
    @abstractmethod
    def execute_instruction(self, instruction: str):
        pass

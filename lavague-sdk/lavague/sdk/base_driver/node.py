from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from PIL import Image


T = TypeVar("T")


class DOMNode(ABC, Generic[T]):
    @property
    @abstractmethod
    def element(self) -> T:
        pass

    @property
    @abstractmethod
    def text(self) -> str:
        pass

    @property
    @abstractmethod
    def value(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def outer_html(self) -> str:
        pass

    @property
    @abstractmethod
    def inner_html(self) -> str:
        pass

    @abstractmethod
    def take_screenshot(self) -> Image.Image:
        pass

    @abstractmethod
    def enter_context(self):
        pass

    @abstractmethod
    def exit_context(self):
        pass

    def __str__(self) -> str:
        with self:
            return self.outer_html

    def __enter__(self):
        self.enter_context()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit_context()

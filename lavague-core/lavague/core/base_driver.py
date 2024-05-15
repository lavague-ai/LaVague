from typing import Tuple, Any, Callable, Optional
from abc import ABC, abstractmethod
from lavague.core.utilities.format_utils import (
    extract_code_from_funct,
    extract_imports_from_lines,
)


class BaseDriver(ABC):
    def __init__(self, url: Optional[str], init_function: Optional[Callable[[], Any]]):
        """Init the driver with the init funtion, and then go to the desired url"""
        self.init_function = (
            init_function if init_function is not None else self.default_init_code
        )
        self.driver = self.init_function()

        # extract import lines for later exec of generated code
        init_lines = extract_code_from_funct(self.init_function)
        self.import_lines = extract_imports_from_lines(init_lines)

        if url is not None:
            self.goto(url)

    @abstractmethod
    def default_init_code(self) -> Any:
        """Code to init the driver, with the imports, since it will be pasted to the beginning of the output"""
        pass

    @abstractmethod
    def destroy(self) -> None:
        """Cleanly destroy the underlying driver"""
        pass

    @abstractmethod
    def get_driver(self) -> Any:
        """Return the expected variable name and the driver object"""
        pass

    @abstractmethod
    def resize_driver(driver, width, height):
        """
        Resize the driver to a targeted height and width.
        """

    @abstractmethod
    def get_url(self) -> Optional[str]:
        """Get the url of the current page"""
        pass

    @abstractmethod
    def go_to_url_code(self, url: str) -> str:
        """Return the code to navigate to the url"""
        pass

    @abstractmethod
    def goto(self, url: str) -> None:
        """Navigate to the url"""
        pass

    @abstractmethod
    def get_html(self, clean: bool = True) -> str:
        """
        Returns the HTML of the current page.
        If clean is True, We remove unnecessary tags and attributes from the HTML.
        Clean HTMLs are easier to process for the LLM.
        """
        pass

    @abstractmethod
    def save_screenshot(self, filename: str) -> None:
        """Save a screenshot to the file filename"""
        pass

    @abstractmethod
    def get_dummy_code(self) -> str:
        """Return testing code relevant for the current driver"""
        pass

    @abstractmethod
    def check_visibility(self, xpath: str) -> bool:
        """Check an element visibility by its xpath"""
        pass

    @abstractmethod
    def exec_code(self, code: str):
        """Exec generated code"""
        pass

    @abstractmethod
    def get_capability(self) -> str:
        """Prompt to explain the llm which style of code he should output and which variables and imports he should expect"""
        pass

from pathlib import Path
from typing import Any, Callable, Optional, Mapping
from abc import ABC, abstractmethod
from lavague.core.utilities.format_utils import (
    extract_code_from_funct,
    extract_imports_from_lines,
)
import time
from datetime import datetime
import hashlib


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
            self.get(url)

    @abstractmethod
    def default_init_code(self) -> Any:
        """Init the driver, with the imports, since it will be pasted to the beginning of the output"""
        pass

    @abstractmethod
    def code_for_init(self) -> str:
        """Extract the code to past to the begining of the final script from the init code"""
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
    def get(self, url: str) -> None:
        """Navigate to the url"""
        pass

    @abstractmethod
    def code_for_get(self, url: str) -> str:
        """Return the code to navigate to the url"""
        pass

    @abstractmethod
    def back(self) -> None:
        """Navigate back"""
        pass

    @abstractmethod
    def code_for_back(self) -> None:
        """Return driver specific code for going back"""
        pass

    @abstractmethod
    def get_html(self, clean: bool = True) -> str:
        """
        Returns the HTML of the current page.
        If clean is True, We remove unnecessary tags and attributes from the HTML.
        Clean HTMLs are easier to process for the LLM.
        """
        pass

    def save_screenshot(self, current_screenshot_folder: Path) -> str:
        """Save the screenshot data to a file and return the path. If the screenshot already exists, return the path. If not save it to the folder."""

        new_screenshot = self.get_screenshot_as_png()
        hasher = hashlib.md5()
        hasher.update(new_screenshot)
        new_hash = hasher.hexdigest()
        new_screenshot_name = f"{new_hash}.png"
        new_screenshot_full_path = current_screenshot_folder / new_screenshot_name

        # If the screenshot does not exist, save it
        if not new_screenshot_full_path.exists():
            with open(new_screenshot_full_path, "wb") as f:
                f.write(new_screenshot)
        return str(new_screenshot_full_path)

    def is_bottom_of_page(self) -> bool:
        return self.execute_script(
            "return (window.innerHeight + window.scrollY) >= document.body.scrollHeight;"
        )

    def get_screenshots_whole_page(self) -> list[str]:
        """Take screenshots of the whole page"""
        screenshot_paths = []

        current_screenshot_folder = self.get_current_screenshot_folder()

        while True:
            # Saves a screenshot
            screenshot_path = self.save_screenshot(current_screenshot_folder)
            screenshot_paths.append(screenshot_path)
            self.execute_script("window.scrollBy(0, (window.innerHeight / 1.5));")
            time.sleep(0.5)

            if self.is_bottom_of_page():
                break
        return screenshot_paths

    @abstractmethod
    def check_visibility(self, xpath: str) -> bool:
        """Check an element visibility by its xpath"""
        pass

    @abstractmethod
    def get_highlighted_element(self, generated_code: str):
        """Return the page elements that generated code interact with"""
        pass

    @abstractmethod
    def exec_code(
        self,
        code: str,
        globals: dict[str, Any] = None,
        locals: Mapping[str, object] = None,
    ):
        """Exec generated code"""
        pass

    @abstractmethod
    def execute_script(self, js_code: str) -> Any:
        """Exec js script in DOM"""
        pass

    @abstractmethod
    def code_for_execute_script(self, js_code: str):
        """return driver specific code to execute js script in DOM"""
        pass

    @abstractmethod
    def get_capability(self) -> str:
        """Prompt to explain the llm which style of code he should output and which variables and imports he should expect"""
        pass

    def get_obs(self) -> dict:
        """Get the current observation of the driver"""
        current_screenshot_folder = self.get_current_screenshot_folder()
        # We take a screenshot and computes its hash to see if it already exists
        self.save_screenshot(current_screenshot_folder)

        url = self.get_url()
        html = self.get_html()
        obs = {
            "html": html,
            "screenshots_path": str(current_screenshot_folder),
            "url": url,
            "date": datetime.now().isoformat(),
        }

        return obs

    def get_current_screenshot_folder(self) -> Path:
        url = self.get_url()
        screenshots_path = Path("./screenshots")
        screenshots_path.mkdir(exist_ok=True)

        current_url = url.replace("://", "_").replace("/", "_")
        hasher = hashlib.md5()
        hasher.update(current_url.encode("utf-8"))

        current_screenshot_folder = screenshots_path / hasher.hexdigest()
        current_screenshot_folder.mkdir(exist_ok=True)
        return current_screenshot_folder

    @abstractmethod
    def get_screenshot_as_png(self) -> bytes:
        pass

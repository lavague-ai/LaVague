from abc import ABC, abstractmethod
import re
from jsonschema import validate, ValidationError
import yaml
import json
from typing import Any, Dict


class ExtractionError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return f"Error extracting the object: {self.args[0]}"


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> str:
        pass

    @abstractmethod
    def extract_as_object(self, text: str) -> Any:
        pass


class YamlFromMarkdownExtractor(BaseExtractor):
    """
    Extractor for the prompts that end with (or similar to) the following:

    --------------------------------------------
    Completion:
    --------------------------------------------
    """

    def extract(self, markdown_text: str) -> str:
        # Pattern to match the first ```yaml ``` code block
        pattern = r"```yaml(.*?)```"

        # Using re.DOTALL to make '.' match also newlines
        match = re.search(pattern, markdown_text, re.DOTALL)
        if match:
            # Return the first matched group, which is the code inside the ```python ```
            return match.group(1).strip()
        else:
            # Return None if no match is found
            return None

    def extract_as_object(self, text: str):
        return yaml.safe_load(self.extract(text))


class JsonFromMarkdownExtractor(BaseExtractor):
    """
    Extractor for the prompts that end with (or similar to) the following:

    --------------------------------------------
    Completion:
    --------------------------------------------
    """

    def extract(self, markdown_text: str, shape_validator=None) -> str:
        # Pattern to match the first ```json ``` code block
        pattern = r"```json(.*?)```"

        # Using re.DOTALL to make '.' match also newlines
        match = re.search(pattern, markdown_text, re.DOTALL)

        if shape_validator:
            try:
                # checks if the json returned from the llm matchs the schema
                validate(
                    instance=json.loads(match.group(1).strip()), schema=shape_validator
                )
            except json.JSONDecodeError:
                raise ExtractionError("Invalid JSON format")
            except ValidationError:
                raise ExtractionError("JSON does not match schema")
        else:
            if match:
                # Return the first matched group, which is the code inside the ```python ```
                return match.group(1).strip()
            else:
                # Return None if no match is found
                return None

    def extract_as_object(self, text: str):
        return json.loads(self.extract(text))


class PythonFromMarkdownExtractor(BaseExtractor):
    """
    Extractor for the prompts that end with (or similar to) the following:

    --------------------------------------------
    Completion:
    --------------------------------------------
    """

    def extract(self, markdown_text: str) -> str:
        # Pattern to match the first ```python ``` code block
        pattern = r"```python(.*?)```"

        # Using re.DOTALL to make '.' match also newlines
        match = re.search(pattern, markdown_text, re.DOTALL)
        if match:
            # Return the first matched group, which is the code inside the ```python ```
            return match.group(1).strip()
        else:
            # Return None if no match is found
            return None

    def extract_as_object(self, text: str):
        return eval(self.extract(text))


class UntilEndOfMarkdownExtractor(BaseExtractor):
    """
    Extractor for the prompts that end with (or similar to) the following:

    --------------------------------------------
    Completion:
    ```python
    # Let's proceed step by step.
    --------------------------------------------
    """

    def extract(self, text: str) -> str:
        return text.split("```")[0]

    def extract_as_object(self, text: str) -> Any:
        return self.extract(text)


class DynamicExtractor(BaseExtractor):
    """
    Extractor for typed markdown blocks
    """

    def __init__(self):
        self.extractors: Dict[str, BaseExtractor] = {
            "json": JsonFromMarkdownExtractor(),
            "yaml": YamlFromMarkdownExtractor(),
            "python": PythonFromMarkdownExtractor(),
        }

    def get_type(self, text: str) -> str:
        types_pattern = "|".join(self.extractors.keys())
        pattern = rf"```({types_pattern}).*?```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            raise ValueError(f"No extractor pattern can be found from {text}")

    def extract(self, text: str) -> str:
        type = self.get_type(text)
        return self.extractors[type].extract(text)

    def extract_as_object(self, text: str) -> Any:
        type = self.get_type(text)
        return self.extractors[type].extract_as_object(text)

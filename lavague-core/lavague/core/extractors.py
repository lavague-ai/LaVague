from abc import ABC, abstractmethod
import re
from jsonschema import validate, ValidationError
import yaml
import json
from typing import Any, Dict, Tuple


def extract_xpaths_from_html(html):
    r_get_xpaths_from_html = r'xpath=["\'](.*?)["\']'
    xpaths = re.findall(r_get_xpaths_from_html, html)
    return xpaths


def extract_xpath_from_action(content):
    # Regular expression to match XPath values
    xpath_pattern = r'xpath:\s*"([^"]*)"'

    # Find all matches in the content
    xpaths = re.findall(xpath_pattern, content)

    return xpaths


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
        yml_str = markdown_text.strip()
        # Pattern to match the first ```yaml ``` code block
        pattern = r"```(?:yaml|yml|\n)(.*?)```"

        # Using re.DOTALL to make '.' match also newlines
        match = re.search(pattern, markdown_text, re.DOTALL)
        if match:
            # Return the first matched group, which is the code inside the ```python ```
            yml_str = match.group(1).strip()
        cleaned_yml = re.sub(r"^```.*\n|```$", "", yml_str, flags=re.DOTALL)
        try:
            yaml.safe_load(cleaned_yml)
            return cleaned_yml
        except yaml.YAMLError:
            # retry with extra quote in case of truncated output
            cleaned_yml += '"'
            try:
                yaml.safe_load(cleaned_yml)
                return cleaned_yml
            except yaml.YAMLError:
                # Truncate after last full YAML action if output was cut off mid-action
                truncated = self._truncate_after_last_action(cleaned_yml)
                if truncated and truncated != cleaned_yml:
                    return truncated
                return None

    def _truncate_after_last_action(self, yml_str: str) -> str:
        """
        Truncate YAML string after the last complete action (key-value pair under a
        top-level key), then append three backticks so the block is syntactically valid.
        This handles cases where the LLM output was cut off by max_tokens mid-action.
        """
        lines = yml_str.rstrip().split('\n')
        if not lines:
            return yml_str

        # Identify the last line that looks like a complete action:
        # a "- key: value" or "key: value" entry at any indentation level
        action_pattern = re.compile(r'^(\s*-\s+\w+:|^\s*\w+:)\s*')

        last_complete_idx = -1
        for idx, line in enumerate(lines):
            if action_pattern.match(line):
                last_complete_idx = idx

        if last_complete_idx >= 0:
            truncated_lines = lines[:last_complete_idx + 1]
            truncated = '\n'.join(truncated_lines) + '\n```'
            # Verify the result is valid YAML
            try:
                yaml.safe_load(truncated)
                return truncated
            except yaml.YAMLError:
                pass
        return yml_str

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
            "yml": YamlFromMarkdownExtractor(),
            "python": PythonFromMarkdownExtractor(),
        }

    def get_type(self, text: str) -> Tuple[str, str]:
        types_pattern = "|".join(self.extractors.keys())
        pattern = rf"```({types_pattern}).*?```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip(), text
        else:
            # Check for opening backticks with type but no closing backticks (max_tokens cut-off)
            truncated_pattern = rf"```({types_pattern}).*"
            truncated_match = re.search(truncated_pattern, text, re.DOTALL)
            if truncated_match:
                type_str = truncated_match.group(1).strip()
                # Check if content after the opening backticks looks like YAML/JSON/action content
                content_after_type = truncated_match.group(0)[len(f"```{type_str}"):].strip()
                if content_after_type:
                    # Pass it through the extractor which will handle truncation
                    return type_str, text
            # Try to auto-detect first matching extractor, and remove extra ```(type)``` wrappers
            cleaned_text = re.sub(r"^```.*\n|```$", "", text, flags=re.DOTALL)
            for type, extractor in self.extractors.items():
                try:
                    value = extractor.extract(cleaned_text)
                    if value:
                        return type, value
                except:
                    pass
            raise ValueError(f"No extractor pattern can be found from {text}")

    def extract(self, text: str) -> str:
        type, target_text = self.get_type(text)
        return self.extractors[type].extract(target_text)

    def extract_as_object(self, text: str) -> Any:
        type, target_text = self.get_type(text)
        return self.extractors[type].extract_as_object(target_text)

from abc import ABC, abstractmethod
import re
import json
from jsonschema import validate, ValidationError

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> str:
        pass


class JsonFromMarkdownExtractor(BaseExtractor):
    """
    Extractor for the prompts that end with (or similar to) the following:

    --------------------------------------------
    Completion:
    --------------------------------------------
    """
   
    def extract(self, markdown_text: str, action_shape_validator = None) -> str:
        # Validate the JSON format
        
        # Pattern to match the first ```python ``` code block
        pattern = r"```json(.*?)```"

        # Using re.DOTALL to make '.' match also newlines
        match = re.search(pattern, markdown_text, re.DOTALL)
        
        if action_shape_validator:
            try:
                #checks if the json returned from the llm matchs the schema
                validate(instance=json.loads(match.group(1).strip()), schema=action_shape_validator)
            except json.JSONDecodeError as e:
                raise(f"Invalid JSON format: {e}")
            except ValidationError as e:
                raise(f"JSON does not match schema: {e}")
        else: 
            if (match):
                # Return the first matched group, which is the code inside the ```python ```
                return match.group(1).strip()
            else:
                # Return None if no match is found
                return None



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

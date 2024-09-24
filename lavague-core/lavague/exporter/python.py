from contextlib import contextmanager
import inspect
import re
from functools import wraps
from typing import Callable, Optional, List
from lavague.exporter.base import TrajectoryExporter
from lavague.action.base import ActionType
from lavague.action.navigation import NavigationOutput
from lavague.action.extraction import ExtractionOutput
from lavague.trajectory import Trajectory

# TODO: this is AI generated. Please double check.
class PythonExporter(TrajectoryExporter):
    # TODO: this is AI generated. Please double check.
    """
    A class for exporting trajectories (sequences of actions) into Python code.

    This class provides a framework for translating various types of actions
    (like clicking, hovering, extracting data, etc.) into Python code snippets
    that can be used in test scripts or automation tasks.

    Key features:
    1. Translates method code into Python strings, replacing action attribute
       references with their actual values.
    2. Extracts method bodies, removing definitions and filtering out excluded functions.
    3. Supports excluding specific methods from export using the @exclude_from_export decorator.
    4. Provides placeholder methods for different action types (click, hover, extract, etc.)
       to be implemented by subclasses.
    5. Generates setup and teardown code for trajectories.
    6. Translates specific action types into Python code.

    This class is designed to be extended by more specific exporters, such as
    PythonSeleniumExporter and QASeleniumExporter, which can implement logic
    for translating actions into Selenium-based Python code and potentially
    incorporate AI-generated test assertions.
    """

    @classmethod
    def translate(cls, method: Callable, output: NavigationOutput, string_only: bool = True) -> Optional[str]:
        """Takes the code of method, replace each use of the 'action' parameter with the actual action attributes.
        Replacement is done only on attributes of the action used in the method.
        """
        source = inspect.getsource(method)

        # Remove leading whitespace and the method definition
        lines = source.split('\n')[1:]
        indentation = len(lines[0]) - len(lines[0].lstrip())
        source = '\n'.join(line[indentation:] for line in lines)
        
        # Find all action attribute accesses
        attribute_pattern = r'output\.(\w+)'
        attributes = re.findall(attribute_pattern, source)

        # Replace action attribute accesses with their actual values
        for attr in attributes:
            if hasattr(output, attr):
                value = getattr(output, attr)
                if isinstance(value, str):
                    value = f"'{value}'"
                else:
                    if string_only:
                        raise ValueError(f"Unsupported type for attribute {attr}: {type(value)}, expected string")
                    else:
                        # Raise a warning that converting non string to string might lead to unpredictable outcomes
                        print(f"Warning: Converting non-string attribute {attr} to string. This might lead to unpredictable outcomes.")
                        value = str(value)
                source = re.sub(f'output\.{attr}', str(value), source)
        
        # Filter out lines within exclude_from_export context
        filtered_lines = []
        for line in source.split('\n'):
            if "raise NotImplementedError" in line:
                # Extract the original error message and raise it
                error_message = line.split("NotImplementedError(", 1)[1].rsplit(")", 1)[0].strip('"\'')
                raise NotImplementedError(error_message)
            
            filtered_lines.append(line)
        
        filtered_source = '\n'.join(filtered_lines)
        return filtered_source.strip() or None
    
    @classmethod
    def extract_method_body(cls, method: Callable) -> Optional[str]:
        """
        Extracts the body of a method, removing the method definition and filtering out excluded functions.
        """
        source = inspect.getsource(method)

        # Remove leading whitespace and the method definition
        lines = source.split('\n')[1:]
        indentation = len(lines[0]) - len(lines[0].lstrip())
        source = '\n'.join(line[indentation:] for line in lines)
        
        return source
    
    def setup(self, trajectory: Trajectory):
        raise NotImplementedError("setup is not implemented")
    
    def teardown(self, trajectory: Trajectory):
        raise NotImplementedError("teardown is not implemented")
    
    def click(self, action: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("click is not implemented")

    def hover(self, action: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("hover is not implemented")

    def extract(self, action: ExtractionOutput) -> Optional[str]:
        raise NotImplementedError("extract is not implemented")
    
    def set_value(self, action: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("set_value is not implemented")

    def type_key(self, action: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("type_key is not implemented")

    def scroll(self, action: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("scroll is not implemented")
    
    def generate_setup(self, trajectory: Trajectory) -> str | None:
        return self.extract_method_body(self.setup)

    def generate_teardown(self, trajectory: Trajectory) -> str | None:
        return self.extract_method_body(self.teardown)

    def translate_click(self, action: NavigationOutput) -> Optional[str]:
        return self.translate(self.click, action)

    def translate_hover(self, action: NavigationOutput) -> Optional[str]:
        return self.translate(self.hover, action)

    def translate_extract(self, action: ExtractionOutput) -> Optional[str]:
        return self.translate(self.extract, action)
    
    def translate_set_value(self, action: NavigationOutput) -> Optional[str]:
        return self.translate(self.set_value, action)

    def translate_type_key(self, action: NavigationOutput) -> Optional[str]:
        return self.translate(self.type_key, action)

    def translate_scroll(self, action: NavigationOutput) -> Optional[str]:
        return self.translate(self.scroll, action)

from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

class PythonSeleniumExporter(PythonExporter):
    def setup(self, trajectory: Trajectory):
        # Setup of the driver
        from selenium import webdriver
        from selenium.webdriver.remote.webdriver import WebDriver
        from selenium.webdriver.common.by import By

    def teardown(self, trajectory: Trajectory):
        # We destroy the driver
        driver: WebDriver = self.get_driver()
        driver.quit()

    def get_driver(self) -> WebDriver:
        pass

    def click(self, action: NavigationOutput) -> Optional[str]:
        driver = self.get_driver()
        driver.find_element(By.XPATH, action.xpath).click()

    def hover(self, action: NavigationOutput) -> Optional[str]:
        driver = self.get_driver()
        driver.find_element(By.XPATH, action.xpath).hover()

    def extract(self, action: ExtractionOutput) -> Optional[str]:
        
        driver = self.get_driver()
        driver.find_element(By.XPATH, action.xpath).text

from llama_index.core.base.llms.base import BaseLLM

TEST_PROMPT_TEMPLATE = """
You are an AI system specialized in generating web tests from specs.
You are povided with:
- some test specs about a whole scenario
- an element extracted from the current page to be tested
You can assume that the provided element is relevant to the test scenario and that we are on the right page.
Only focus on assertions that concern the current element, do not extrapolate asserts that rely on other elements. 
Your output must contain only code for the assertions, there is no need for boilerplate code. You can assume that the element has been resolved already and is called `element`.

Your goal is to generate Python assertions to be used in a test script to test the extracted element.

Here are previous examples:
---
Specs: When a user logs in successfully, they should see a welcome message with their username on the dashboard.
Xpath: //*[@id="welcome-message"]
Description: Welcome message displayed on the dashboard after successful login
Text: Welcome back, JohnDoe! Your last login was on 2024-09-20 at 15:30.
Outer HTML: <div id="welcome-message" class="dashboard-header">Welcome back, JohnDoe! Your last login was on 2024-09-20 at 15:30.</div>
Test:```python
# Let's think step by step

# 1. The welcome message should contain the user's name
# 2. The message should start with a greeting
# 3. It should include the last login date and time
# 4. The element should have the correct ID
# 5. The element should have the expected class
# 6. The element should be visible on the page

# Assert that the welcome message contains the user's name
assert "JohnDoe" in element.text, f"User's name not found in welcome message. Actual text: {{element.text}}"

# Assert that the welcome message starts with the expected greeting
assert element.text.startswith("Welcome back"), f"Welcome message doesn't start with expected greeting. Actual text: {{element.text}}"

# Assert that the welcome message contains a date and time
import re
date_time_pattern = r'\d{{4}}-\d{{2}}-\d{{2}} at \d{{2}}:\d{{2}}'
assert re.search(date_time_pattern, element.text), f"Date and time not found in expected format. Actual text: {{element.text}}"

# Assert that the element has the correct ID
assert element.get_attribute("id") == "welcome-message", f"Element ID is incorrect. Expected 'welcome-message', got '{{element.get_attribute('id')}}'"

# Assert that the element has the expected class
assert "dashboard-header" in element.get_attribute("class"), f"Element doesn't have expected class 'dashboard-header'. Actual classes: {{element.get_attribute('class')}}"

# Assert that the element is visible
assert element.is_displayed(), "Welcome message element is not visible on the page"
```
---

Here is the next example to complete:
Specs: {test_specs}
Xpath: {xpath}
Description: {description}
Text: {text}
Outer HTML: {outer_html}
Test:
```python
"""

import re

def extract_code_block(code_block):
    pattern = r'```(?:python)?\n(.*?)\n```'
    match = re.search(pattern, code_block, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    else:
        return "No code block found"

class QASeleniumExporter(PythonSeleniumExporter):

    def __init__(self, llm: BaseLLM = None):
        if llm is None:
            llm = get_default_context().llm
        self.llm = llm

    def extract(self, action_output: ExtractionOutput) -> Optional[str]:
        driver = self.get_driver()
        element = driver.find_element(By.XPATH, action_output.xpath)

    def export(self, trajectory: Trajectory, scenario: str) -> str:
        setup: Optional[str] = self.generate_setup(trajectory)
        teardown: Optional[str] = self.generate_teardown(trajectory)
        translated_actions: List[Optional[str]] = []
        for action in trajectory.actions:
            if action.action_type == ActionType.NAVIGATION:
                translated_action: Optional[str] = self.translate_action(action)
                translated_actions.append(translated_action)
            elif action.action_type == ActionType.EXTRACTION:
                translated_action_lines: List[str] = []
                for output in action.action_output:
                    output: ExtractionOutput
                    # First we get the element
                    translated_action_lines.append(self.translate_extract(output))
                    # Then we generate asserts for it   
                    xpath: str = output.xpath
                    description: str = output.description
                    text: str = output.text
                    outer_html: str = output.outer_html

                    test_prompt = TEST_PROMPT_TEMPLATE.format(
                        test_specs=scenario,
                        xpath=xpath,
                        description=description,
                        text=text,
                        outer_html=outer_html,
                    )

                    test_response = self.llm.complete(test_prompt).text
                    generated_asserts: str = extract_code_block(test_response)
                    translated_action_lines.append(generated_asserts)

                translated_action: str = self.merge_code(*translated_action_lines)
                translated_actions.append(translated_action)
        translated_actions_str: str = self.merge_code(*translated_actions)
        return self.merge_code(setup, translated_actions_str, teardown)
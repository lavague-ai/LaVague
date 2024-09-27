from llama_index.core.base.llms.base import BaseLLM
import re
from typing import Optional, List
from lavague.action.base import ActionType
from lavague.action.extraction import ExtractionOutput
from lavague.trajectory import TrajectoryData
from lavague.exporter.python_selenium import PythonSeleniumExporter
from lavague.exporter.python import exclude_from_export
from selenium.webdriver.common.by import By


class QASeleniumExporter(PythonSeleniumExporter):
    def __init__(self, llm: BaseLLM, time_between_actions: float = 2.5):
        self.llm = llm
        self.time_between_actions = time_between_actions

    def extract(self, action_output: ExtractionOutput) -> Optional[str]:
        with exclude_from_export():
            driver = self.get_driver()
        element = driver.find_element(By.XPATH, action_output.xpath)

    def export(self, trajectory: TrajectoryData) -> str:
        setup: Optional[str] = self.generate_setup(trajectory)
        teardown: Optional[str] = self.generate_teardown(trajectory)
        translated_actions: List[Optional[str]] = []
        for action in trajectory.actions:
            if action.action_type == ActionType.NAVIGATION:
                navigation_action = self.translate_action(action) or ""
                navigation_action += f"\ntime.sleep({self.time_between_actions})"
                translated_actions.append(navigation_action)

            elif action.action_type == ActionType.EXTRACTION:
                translated_action_lines: List[str] = []
                for output in action.action_output:
                    output: ExtractionOutput
                    # First we get the element
                    translated_action_lines.append(self.translate_extract(output) or "")
                    # Then we generate asserts for it
                    xpath: str = output.xpath
                    description: str = output.description
                    text: str = output.text
                    outer_html: str = output.outer_html

                    test_prompt = TEST_PROMPT_TEMPLATE.format(
                        test_specs=trajectory.objective,
                        xpath=xpath,
                        description=description,
                        text=text,
                        outer_html=outer_html,
                    )

                    test_response = self.llm.complete(test_prompt).text
                    generated_asserts: str = extract_code_block(test_response)
                    translated_action_lines.append(generated_asserts)
                    translated_action_lines.append(
                        f"\ntime.sleep({self.time_between_actions})"
                    )

                translated_action: str = self.merge_code(*translated_action_lines)

                translated_actions.append(translated_action)

        translated_actions_str: str = self.merge_code(*translated_actions)
        return self.merge_code(setup, translated_actions_str, teardown)


def extract_code_block(code_block):
    pattern = r"```(?:python)?\n(.*?)\n```"
    match = re.search(pattern, code_block, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return "No code block found"


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

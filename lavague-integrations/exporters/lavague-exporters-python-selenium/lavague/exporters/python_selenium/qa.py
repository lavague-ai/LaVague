from litellm import completion
import re
from typing import Optional, List
from lavague.sdk.action.base import ActionType
from lavague.sdk.action.extraction import ExtractionOutput
from lavague.sdk.trajectory import TrajectoryData
from lavague.exporters.python_selenium import PythonSeleniumExporter
from lavague.exporters.python import exclude_from_export
from selenium.webdriver.common.by import By

SYSTEM_PROMPT = """You are an AI system specialized in generating web tests from specs.
You are povided with:
- some test specs about a whole scenario
- an element extracted from the current page to be tested
You can assume that the provided element is relevant to the test scenario and that we are on the right page.
Only focus on assertions that concern the current element, do not extrapolate asserts that rely on other elements. 
Your output must contain only code for the assertions, there is no need for boilerplate code. You can assume that the element has been resolved already and is called `element`.

Your goal is to generate Python assertions to be used in a test script to test the extracted element.
Be concise: only provide necessary and sufficient assertions for the purpose of the test.

Here are previous examples:
---
Specs: When a user logs in successfully, they should see a welcome message with their username on the dashboard.
Context: 
```python
import re
element = driver.find_element(By.XPATH, "//div[@id='welcome-message' and @class='dashboard-header']")
```
Element description: Welcome message displayed on the dashboard after successful login
Element text: Welcome back, JohnDoe! Your last login was on 2024-09-20 at 15:30.
Element outer HTML: <div id="welcome-message" class="dashboard-header">Welcome back, JohnDoe! Your last login was on 2024-09-20 at 15:30.</div>
Test:```python
# Let's think step by step

# Verify the greeting and personalization
assert element.text.startswith("Welcome back, JohnDoe"), f"Greeting should be personalized. Found: {element.text[:30]}..."

# Validate the presence of login information
assert "last login was on" in element.text, f"Login info should be present. Text: {element.text}"

# Ensure the welcome message is visible
assert element.is_displayed(), "Welcome message should be visible on the dashboard"
```
Specs:
Feature: Product Search and Filtering
  As a customer
  I want to search for products and apply filters
  So that I can find the items I'm interested in quickly

Scenario: Search for laptops and filter by price range
  Given I am on the electronics category page
  When I search for "laptop" in the search bar
  And I apply a price filter for items between $500 and $1000
  Then I should see a list of laptop products
  And all displayed products should be within the specified price range
  And the active filter should be visible

Context:
element = driver.find_element(By.XPATH, "/html/body/div[@id='main-content']/div[@class='search-results-container']/div[@class='sidebar']/div[@id='active-filters']")
Element description: Active filter display showing the current price range filter applied to the search results
Element text: Price: $500 - $1000
Element outer HTML: 
<div id="active-filters" class="filter-tags">
  <span class="filter-tag">Price: $500 - $1000 <button class="remove-filter" aria-label="Remove price filter">×</button></span>
</div>
Test:
```python
# Let's think step by step

# Verify the presence and correctness of the price filter
assert "Price: $500 - $1000" in element.text, f"Price filter should be visible and correct. Found: {element.text}"

# Ensure the filter tag is displayed
assert element.is_displayed(), "Active filter should be visible on the page"

# Check for the presence of a remove button to ensure filter can be cleared
remove_button = element.find_element(By.CLASS_NAME, "remove-filter")
assert remove_button.is_displayed(), "Remove filter button should be present"

# Validate the accessibility label of the remove button
assert remove_button.get_attribute("aria-label") == "Remove price filter", f"Remove button should have correct aria-label. Found: {remove_button.get_attribute('aria-label')}"
```
---
"""

PROMPT_TEMPLATE = """Here is the next example to complete:
Specs: {test_specs}
Context: {context}
Element description: {description}
Element text: {text}
Element outer HTML: {outer_html}
Test:"""

class QASeleniumExporter(PythonSeleniumExporter):
    def __init__(self, model: str = "gpt-4o", time_between_actions: float = 2.5):
        self.model = model
        self.time_between_actions = time_between_actions

    def extract(self, action_output: ExtractionOutput) -> Optional[str]:
        with exclude_from_export():
            driver = self.get_driver()
        element = driver.find_element(By.XPATH, action_output.xpath)

    def export(self, trajectory: TrajectoryData, scenario: str) -> str:
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
                    import_context = self.translate_boilerplate(self.setup, trajectory)
                    element_context = self.translate(self.extract, output)
                    context = "\n".join([import_context, element_context])

                    description: str = output.description
                    text: str = output.text
                    outer_html: str = output.outer_html

                    prompt = PROMPT_TEMPLATE.format(
                        test_specs=scenario, 
                        context=context,
                        description=description,
                        text=text,
                        outer_html=outer_html,
                    )
                    test_response = completion(
                        model = self.model,
                        messages = [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ]
                    ).choices[0].message.content           

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
from lavague.core.base_engine import ActionResult, BaseEngine
from lavague.core.logger import AgentLogger
from llama_index.core.multi_modal_llms.base import MultiModalLLM
from lavague.core.context import get_default_context
from llama_index.core import PromptTemplate
from lavague.core.base_driver import BaseDriver
from llama_index.core import SimpleDirectoryReader

import yaml

def load_yaml_from_string(yaml_string):
    try:
        return yaml.safe_load(yaml_string)
    except yaml.YAMLError as e:
        print(f"Error loading YAML string: {e}")
        return None

PREVIOUS_EXAMPLES = """
Instruction: Click on Sign In / Register

Thoughts:
- The "Sign in / Register" button is located at the top right.
- The button is highlighted with the ID "37".
- There is no other element that matches the direction, therefore the most likely outcome is "37".
Output: 
- action:
    name: click
    args:
      id: 37
---
Instruction: Type 'What is love' in the search bar

Thoughts:
- Given the instruction, the most likely element to interact with is the search bar at the top with the ID "0".
- I will set the value of the search bar to "What is love".
Output: 
- action:
    name: click
    args:
      id: 0
      value: "What is love"
---
Instruction: In the contact form, fill out the "Name" field with "John Doe", the "Email" field with "john@example.com", and click the submit button
Thoughts:

- We need to identify multiple elements in a form and interact with them in sequence.
- The "Name" field is highlighted with ID "23".
- The "Email" field is highlighted with ID "24".
- The submit button is highlighted with ID "25".
- We'll need to perform multiple actions in the correct order.

Output:
- action:
    name: setValue
    args:
      id: 23
      value: "John Doe"
- action:
    name: setValue
    args:
      id: 24
      value: "john@example.com"
- action:
    name: click
    args:
      id: 25
"""

SOM_PROMPT_TEMPLATE = """
You are an AI assistant tasked with helping navigate web interfaces.
You are provided with screenshots with different elements already highlighted and their corresponding ID. 
Your goal is to output actions in YAML format that can be used to interact with the elements.
The actions available are:

Name: click
Description: Click on an element with a specific xpath
Arguments:
  - id (int)

Name: setValue
Description: Focus on and set the value of an input element with a specific xpath
Arguments:
  - id (int)
  - value (string)

Name: setValueAndEnter
Description: Like "setValue", except then it presses ENTER. Use this tool can submit the form when there's no "submit" button.
Arguments:
  - id (int)
  - value (string)

Your goal is to output in YAML 

- action:
    name: click
    args:
      id: "/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/a"
- action:
    name: click
    args:
      xpath: "/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/div/tab[1]/a"

Your output must be in the following format:
- Thoughts: explanation of the process to derive the output
- Action: the output action in YAML format

Here are previous examples:
{previous_examples}

Here is the current example to classify:

Instruction: {instruction}

Thoughts:
"""

def process_elements_with_highlights(driver):
    js_script = """
    function getElementsFromXPaths(xpaths) {
        return xpaths.map((xpath, index) => {
            try {
                const element = document.evaluate(
                    xpath, 
                    document, 
                    null, 
                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null
                ).singleNodeValue;
                if (element) {
                    highlightElement(element);
                    addIdOverlay(element, index);
                    return { element, xpath };
                }
            } catch (e) {
                console.error('Error processing XPath:', xpath, e);
            }
            return null;
        }).filter(item => item !== null);
    }

    function highlightElement(element) {
        element.setAttribute('data-original-style', element.getAttribute('style') || '');
        element.style.border = '2px solid red';
    }

    function addIdOverlay(element, id) {
        const rect = element.getBoundingClientRect();
        const overlay = document.createElement('div');
        overlay.textContent = id;
        overlay.className = 'selenium-id-overlay';
        overlay.style.position = 'absolute';
        overlay.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
        overlay.style.color = 'white';
        overlay.style.padding = '2px 5px';
        overlay.style.borderRadius = '3px';
        overlay.style.fontSize = '20px';
        overlay.style.zIndex = '10000';
        overlay.style.pointerEvents = 'none';
        
        overlay.style.left = (rect.left - 25) + 'px';
        overlay.style.top = (rect.top - 25) + 'px';
        
        if (rect.left < 30) {
            overlay.style.left = rect.right + 'px';
        }
        
        if (rect.top < 30) {
            overlay.style.top = rect.bottom + 'px';
        }
        
        document.body.appendChild(overlay);
    }

    const xpaths = arguments[0];
    return getElementsFromXPaths(xpaths);
    """
    
    xpaths = driver.get_possible_interactions().keys()
    result = driver.execute_script(js_script, list(xpaths))
    
    # Create id_to_xpath dictionary
    id_to_xpath = {i: item['xpath'] for i, item in enumerate(result)}
    
    return id_to_xpath

def remove_highlights(driver):
    js_script = """
    function removeHighlight(element) {
        const originalStyle = element.getAttribute('data-original-style');
        if (originalStyle === null) {
            element.removeAttribute('style');
        } else {
            element.setAttribute('style', originalStyle);
        }
        element.removeAttribute('data-original-style');
    }
    
    const elements = document.querySelectorAll('[data-original-style]');
    elements.forEach(removeHighlight);
    """
    driver.execute_script(js_script)

def remove_id_overlays(driver):
    js_script = """
    const overlays = document.querySelectorAll('.selenium-id-overlay');
    overlays.forEach(overlay => {
        overlay.remove();
    });
    """
    driver.execute_script(js_script)

def execute_action(driver: BaseDriver, action_list: str):
    """Executes the action"""
    for item in action_list:
        action_name = item["action"]["name"]
        if action_name == "click":
            driver.click(item["action"]["args"]["xpath"])
        elif action_name == "setValue":
            driver.set_value(
                item["action"]["args"]["xpath"], item["action"]["args"]["value"]
            )
        elif action_name == "setValueAndEnter":
            driver.set_value(
                item["action"]["args"]["xpath"],
                item["action"]["args"]["value"],
                True,
            )
        else:
            raise ValueError(f"Invalid action name: {action_name}")

class SoMNavigationEngine(BaseEngine):
    def __init__(
        self,
        driver: BaseDriver,
        mm_llm: MultiModalLLM = None,
        prompt_template: PromptTemplate = None,
        time_between_actions: float = 1.5,
        logger: AgentLogger = None,
        display: bool = False,
    ):
        if mm_llm is None:
            mm_llm: MultiModalLLM = get_default_context().mm_llm
        if prompt_template is None:
            prompt_template = PromptTemplate(SOM_PROMPT_TEMPLATE)
            prompt_template = prompt_template.partial_format(
                previous_examples=PREVIOUS_EXAMPLES
            )

        self.driver: BaseDriver = driver
        self.mm_llm: MultiModalLLM = mm_llm
        self.prompt_template: PromptTemplate = prompt_template
        self.time_between_actions = time_between_actions
        self.logger = logger
        self.display = display
        
    def get_screenshot(self):
        driver = self.driver
        id_to_xpath = process_elements_with_highlights(driver)

        current_screenshot_folder = driver.get_current_screenshot_folder()
        driver.save_screenshot(current_screenshot_folder)
        
        remove_highlights(driver)
        remove_id_overlays(driver)
        
        return current_screenshot_folder, id_to_xpath
        
    def get_action(self, instruction: str):
        
        screenshots_path, id_to_xpath = self.get_screenshot()
        image_documents = SimpleDirectoryReader(screenshots_path).load_data()

        prompt = self.prompt_template.format(instruction=instruction)
        mm_llm_output = self.mm_llm.complete(prompt, image_documents=image_documents).text
        
        yaml_string = mm_llm_output.split("Output:")[1].replace("```","").replace("yaml","")
        
        action_list = load_yaml_from_string(yaml_string)
        
        for action in action_list:
            action_args = action["action"]["args"]
            action_args["xpath"] = id_to_xpath[action_args["id"]]

        return action_list
    def execute_instruction(self, instruction: str) -> ActionResult:
        driver: BaseDriver = self.driver
        
        action_list: str = self.get_action(instruction)
        execute_action(driver, action_list)
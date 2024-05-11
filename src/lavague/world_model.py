import os
from openai import OpenAI
from .prompts import WORLD_MODEL_PROMPT_TEMPLATE
from string import Template
from .format_utils import keep_assignments, return_assigned_variables
from selenium.webdriver.remote.webelement import WebElement
from IPython.display import Image
from abc import ABC, abstractmethod
from typing import Any

def get_highlighted_element(generated_code, driver):

    assignment_code = keep_assignments(generated_code)

    code = f"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
{assignment_code}
    """.strip()

    local_scope = {"driver": driver}

    exec(code, globals(), local_scope)

    variable_names = return_assigned_variables(generated_code)

    elements = []

    for variable_name in variable_names:
        var = local_scope[variable_name]
        if type(var) == WebElement:
            elements.append(var)

    first_element = elements[0]
    driver.execute_script("arguments[0].setAttribute('style', arguments[1]);", first_element, "border: 2px solid red;")
    driver.execute_script("arguments[0].scrollIntoView();", first_element)
    driver.save_screenshot("screenshot.png")
    image = Image("screenshot.png")
    driver.execute_script("arguments[0].setAttribute('style', '');", first_element)
    return image

class AbstractWorldModel(ABC):
    """Abstract class for WorldModel"""

    @abstractmethod
    def get_instruction(self, state: Any, objective: str) -> str:
        """Get instruction from the world model given the current state and objective."""
        raise NotImplementedError("get_instruction method is not implemented")

class GPTWorldModel:
    """Class for Vision-based WorldModel"""

    def __init__(self, examples, api_key: str = None):
        self.prompt_template = WORLD_MODEL_PROMPT_TEMPLATE.safe_substitute(examples=examples)
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError("No api_key is provided or OPENAI_API_KEY environment variable is not set")
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

    def get_instruction(self, state: str, objective: str) -> str:
        """Use GPT4V to generate instruction from the current state and objective."""
        base64_image = state

        prompt = Template(self.prompt_template).safe_substitute(objective=objective)

        model = "gpt-4-turbo"
        messages = [
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": prompt
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high"
                }
                }
            ]
            }
        ]
        response  = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=300, temperature=0.0, seed=42
        )

        output = response.choices[0].message.content
        return output
from .prompts import WORLD_MODEL_PROMPT_TEMPLATE
from string import Template
from abc import ABC, abstractmethod
from typing import Any
import requests

from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.core.multi_modal_llms.generic_utils import load_image_urls
from llama_index.core import SimpleDirectoryReader

import base64
import os

class BaseWorldModel(ABC):
    """Abstract class for WorldModel"""

    @abstractmethod
    def get_instruction(self, state: Any, objective: str) -> str:
        """Get instruction from the world model given the current state and objective."""
        raise NotImplementedError("get_instruction method is not implemented")

class GPTWorldModel(BaseWorldModel):
    """Class for Vision-based WorldModel"""

    def __init__(self, examples, api_key: str = None):
        self.prompt_template = WORLD_MODEL_PROMPT_TEMPLATE.safe_substitute(examples=examples)
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError("No api_key is provided or OPENAI_API_KEY environment variable is not set")
        self.mm_llm = OpenAIMultiModal(model="gpt-4o", max_new_tokens=300, api_key= api_key)

    def get_instruction(self, state: str, objective: str) -> str:
        """Use GPT4V to generate instruction from the current state and objective."""

        prompt = Template(self.prompt_template).safe_substitute(objective=objective)

        base64_image = state
        
        image_data = base64.b64decode(base64_image)

        # Create the 'screenshots' directory if it doesn't exist
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')

        # Save the image data to a PNG file
        with open('screenshots/output.png', 'wb') as file:
            file.write(image_data)
            
        image_documents = SimpleDirectoryReader("./screenshots").load_data()
        
        output = self.mm_llm.complete(prompt, image_documents=image_documents).text

        return output
    
class AzureWorldModel(BaseWorldModel):
    """Class for Vision-based WorldModel"""
    
    def __init__(self, examples: str, api_key: str, endpoint: str):
        self.prompt_template = WORLD_MODEL_PROMPT_TEMPLATE.safe_substitute(examples=examples)
        self.api_key = api_key
        self.endpoint = endpoint
    
    def get_instruction(self, state: str, objective: str) -> str:
        base64_image = state
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }
        
        prompt = self.prompt_template.format(objective=objective)

        # Payload for the request
        payload = {
        "messages": [
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
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
                }
            ]
            }
        ],
        "temperature": 0.0,
        "top_p": 0.95,
        "max_tokens": 800
        }
        
        endpoint = self.endpoint

        # Send request
        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
        except requests.RequestException as e:
            raise SystemExit(f"Failed to make the request. Error: {e}")

        output = response.json()["choices"][0]["message"]["content"]
        return output
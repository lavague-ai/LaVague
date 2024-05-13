import os
from openai import OpenAI
from .prompts import WORLD_MODEL_PROMPT_TEMPLATE
from string import Template
from abc import ABC, abstractmethod
from typing import Any
import requests

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
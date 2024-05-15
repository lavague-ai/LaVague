from typing import Optional
from abc import ABC
import os
import base64

from llama_index.core import PromptTemplate, SimpleDirectoryReader
from llama_index.core.multi_modal_llms import MultiModalLLM

from lavague.core import Context, get_default_context


class WorldModel(ABC):
    """Abstract class for WorldModel"""

    mm_llm: MultiModalLLM
    prompt_template: PromptTemplate

    def __init__(self, examples: str, context: Optional[Context] = None):
        if context is None:
            context = get_default_context()
        self.mm_llm = context.mm_llm
        self.prompt_template = WORLD_MODEL_PROMPT_TEMPLATE.partial_format(
            examples=examples
        )

    @classmethod
    def from_hub(cls, url_slug: str, context: Optional[Context] = None):
        """Instantiate with template from remote hub."""
        import requests

        response = requests.get(
            "https://raw.githubusercontent.com/lavague-ai/LaVague/main/examples/knowledge/"
            + url_slug
            + ".txt"
        )
        if response.status_code == 200:
            instance = cls(response.text, context)
            return instance
        else:
            raise Exception("Failed to fetch prompt template from hub")

    @classmethod
    def from_local(cls, filepath: str, context: Optional[Context] = None):
        """Instantiate with template from local file."""
        if os.path.exists(filepath):
            with open(filepath, "r") as file:
                examples = file.read()
                instance = cls(examples, context)
            return instance
        else:
            raise FileNotFoundError(f"No file found at {filepath}")

    def get_instruction(self, state: str, objective: str) -> str:
        """Use GPT*V to generate instruction from the current state and objective."""

        prompt = self.prompt_template.format(objective=objective)

        base64_image = state

        image_data = base64.b64decode(base64_image)

        # Create the 'screenshots' directory if it doesn't exist
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")

        # Save the image data to a PNG file
        with open("screenshots/output.png", "wb") as file:
            file.write(image_data)

        image_documents = SimpleDirectoryReader("./screenshots").load_data()

        output = self.mm_llm.complete(prompt, image_documents=image_documents).text

        return output


WORLD_MODEL_PROMPT_TEMPLATE = PromptTemplate(
    """
You are an AI system specialized in high level reasoning. Your goal is to generate instructions for other specialized AIs to perform web actions to reach objectives given by humans.
Your inputs are an objective in natural language, as well as a screenshot of the current page of the browser.
Your output are a list of thoughts in bullet points detailling your reasoning, followed by your conclusion on what the next step should be in the form of an instruction.
You can assume the instruction is used by another AI to generate the action code to select the element to be interacted with and perform the action demanded by the human.

The instruction should be detailled as possible and only contain the next step. 
Do not make assumptions about elements you do not see.
If the objective is already achieved in the screenshot, provide the instruction 'STOP'.

Here are previous examples:
${examples}

Objective: ${objective}
Thought:
"""
)

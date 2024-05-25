from __future__ import annotations
from abc import ABC
from PIL import Image
from llama_index.core import PromptTemplate
from llama_index.core.multi_modal_llms import MultiModalLLM
from llama_index.core import SimpleDirectoryReader
from pathlib import Path
from lavague.core.context import Context, get_default_context
from lavague.core.logger import AgentLogger
import time
import yaml

WORLD_MODEL_GENERAL_EXAMPLES = """
Objective:  Go to the first issue you can find
Previous instructions: 
- Click on 'Issues' with the number '28' next to it.
- [FAILED] Click on 'Build and share place where people can suggest their use cases and results #225'
- [FAILED] Click on 'Build and share place where people can suggest their use cases and results #225'
Last engine: Navigation Engine
Current state: 
external_observations:
  vision: '[SCREEENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []

Thoughts:
- The current screenshot shows the issues page of the GitHub repository 'lavague-ai/LaVague'.
- The objective is to go to the first issue.
- Previous instructions have been unsuccessful. A new approach should be used.
- The '#225' seems not to be clickable and it might be relevant to devise an instruction that does not include it. 
Next engine: Navigation Engine
Instruction: Click on the first issue, with title 'Build and share place where people can suggest their use cases and results'
-----
Objective: Find When Llama 3 was released
Previous instructions:
- Click on 'meta-llama/Meta-Llama-3-8B'
Last engine: Navigation Engine
Current state:
external_observations:
  vision: '[SCREEENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []

Thoughts:
- The current screenshot shows the model page for 'meta-llama/Meta-Llama-3-8B' on Hugging Face.
- Hugging Face, is a hub for AI models and datasets, where users can explore and interact with a variety of AI models.
- I am therefore on the right page to find information about the release date of 'Meta-Llama-3-8B'.
- To find the release date, I need to locate the relevant information in the content of the page.
- Therefore the best next step is to use the Python Engine to extract the release date from the content of the page.
Next engine: Python Engine
Instruction: Extract the release date of 'Meta-Llama-3-8B' from the textual content of the page.
-----
Objective: Provide the code to get started with Gemini API
Previous instructions:
- Click on 'Read API docs'
- Click on 'Gemini API quickstart' on the menu
Last engine: Navigation Engine
Current state:
external_observations:
  vision: '[SCREEENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []

Thoughts:
- The current screenshot shows the documentation page for the getting started of Gemini API.
- I am therefore on the right page to find the code to get started with the Gemini API.
- The next step is to provide the code to get started with the Gemini API.
- Therefore I need to use the Python Engine to generate the code to extract the code to get started with the Gemini API from this page.
Next engine: Python Engine
Instruction: Extract the code to get started with the Gemini API from the content of the page.
-----
Objective: Show what is the cheapest product
Previous instructions: []
Last engine: [NONE]
Current state:
external_observations:
  vision: '[SCREEENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []
  
Thoughts:
- The screenshot shows an e-commerce website with various products.
- To find the cheapest product, I need to identify the product with the lowest price.
- There seems to be selectors for sorting products by price on the left side of the page.
- The screenshot only shows part of the selectors for price. I should scroll down to see the full list of products and prices.
Next engine: Navigation Controls
Instruction: SCROLL_DOWN
-----
Objective: What tech stack do we use?
Previous instructions: 
- [FAILED] Locate and click on the "Technology Solutions" link or section to find information about the tech stack.
- [FAILED] Click on the "Technology Solutions" section to explore detailed information about the tech stack.
Last engine: Navigation Engine
Current state: 
external_observations:
  vision: '[SCREEENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []

Thought:
- The screenshot shows a Notion webpage with information about a company called ACME INC.
- It has information about the company, their services, and departments.
- Previous instructions tried to click on "Technology Solutions" without success. This probably means that "Technology Solutions" is not clickable or reachable.
- Other strategies have to be pursued to reach the objective.
- There seems to be information at the end of the screen about departments, with mention of a 'Software development' section that could be promising.
- The best next step is to scroll down to gather more information.
Next engine: Navigation Controls
Instruction: SCROLL_DOWN
-----
Objective: Find the description of the author
Previous instructions:
- Click on 'About the author'
- Extract the description of the author from the content of the page.
Last engine: Python Engine
Current state:
external_observations:
  vision: '[SCREEENSHOT]'
internal_state:
  agent_outputs: [
    'The author is a software engineer with a passion for AI and machine learning. He has worked on various projects and has a blog where he shares his knowledge and experience.'
  ]
  user_inputs: []

Thoughts:
- The screenshot shows the description of the author.
- The description of the author has been successfully extracted from the content of the page.
- The objective has been reached. The search bar of HF is syntaxic not semantic therefore I s
Next engine: STOP
Instruction: STOP
"""

WORLD_MODEL_PROMPT_TEMPLATE = PromptTemplate(
    """
You are an AI system specialized in high level reasoning. Your goal is to generate instructions for other specialized AIs to perform web actions to reach objectives given by humans.
Your inputs are:
- objective ('str'): a high level description of the goal to achieve.
- previous_instructions ('str'): a list of previous steps taken to reach the objective.
- last_engine ('str'): the engine used in the previous step.
- current_state ('dict'): the state of the environment in YAML to use to perform the next step.

Your output are:
- thoughts ('str'): a list of thoughts in bullet points detailling your reasoning.
- next_engine ('str'): the engine to use for the next step.
- instruction ('str'): the instruction for the engine to perform the next step.

Here are the engines at your disposal:
- Python Engine: This engine is used when the task requires doing computing using the current state of the agent. 
It does not impact the outside world and does not navigate.
- Navigation Engine: This engine is used when the next step of the task requires further navigation to reach the goal. 
For instance it can be used to click on a link or to fill a form on a webpage. This engine is heavy and will do complex processing of the current HTML to decide which element to interact with.
- Navigation Controls: This is a simpler engine to do commands that does not require reasoning, which are 'SCROLL_DOWN', 'SCROLL_UP' and 'WAIT'.

Here are guidelines to follow:

# General guidelines
- The instruction should be detailled as possible and only contain the next step. 
- If the objective is already achieved in the screenshot, or the current state contains the demanded information, provide the next engine and instruction 'STOP'.
- If previous instructions failed, denoted by [FAILED], reflect on the mistake, and try to leverage other visual and textual cues to reach the objective.

# Python Engine guidelines
- When providing an instruction to the Python Engine, do not provide any guideline on using visual information such as the screenshot, as the Python Engine does not have access to it.
- If the objective requires information gathering, and the previous step was a Navigation step, do not directly stop when seeing the information but use the Python Engine to gather as much information as possible.

# Navigation guidlines
- If the screenshot provides information but seems insufficient, use navigation controls to further explore the page.
- When providing information for the Navigation Engine, focus on elements that are most likely interactable, such as buttons, links, or forms and be precise in your description of the element to avoid ambiguitiy.
- If several steps have to be taken, provide instructions in bullet points.

Here are previous examples:
{examples}

Here is the next objective:
Objective: {objective}
Previous instructions: 
{previous_instructions}
Last engine: {last_engine}
Current state: 
{current_state}

Thought:
"""
)


class WorldModel(ABC):
    """Abstract class for WorldModel"""

    def __init__(
        self,
        mm_llm: MultiModalLLM = get_default_context().mm_llm,
        prompt_template: PromptTemplate = WORLD_MODEL_PROMPT_TEMPLATE,
        examples: str = WORLD_MODEL_GENERAL_EXAMPLES,
        logger: AgentLogger = None,
    ):
        self.mm_llm: MultiModalLLM = mm_llm
        self.prompt_template: PromptTemplate = prompt_template.partial_format(
            examples=examples
        )
        self.logger: AgentLogger = logger

    @classmethod
    def from_context(
        cls,
        context: Context,
        prompt_template: PromptTemplate = WORLD_MODEL_PROMPT_TEMPLATE,
        examples: str = WORLD_MODEL_GENERAL_EXAMPLES,
    ) -> WorldModel:
        return cls(context.mm_llm, prompt_template, examples)

    def get_instruction(
        self,
        objective: str,
        current_state: dict,
        past: dict,
        observations: dict,
    ) -> str:
        """Use GPT*V to generate instruction from the current state and objective."""
        mm_llm = self.mm_llm
        logger = self.logger
        
        previous_instructions = past["previous_instructions"]
        last_engine = past["last_engine"]
        
        try:
          current_state_str = yaml.dump(current_state, default_flow_style=False)
        except:
          raise Exception("Could not convert current state to YAML")
        
        screenshot: Image.Image = observations["screenshot"]
        
        Path("./screenshots").mkdir(exist_ok=True)
        screenshot.save("./screenshots/screenshot.png")
        image_documents = SimpleDirectoryReader("./screenshots").load_data()
        
        prompt = self.prompt_template.format(
            objective=objective,
            previous_instructions=previous_instructions,
            last_engine=last_engine,
            current_state=current_state_str,
        )

        start = time.time()
        mm_llm_output = mm_llm.complete(prompt, image_documents=image_documents).text
        end = time.time()
        world_model_inference_time = end - start
        
        if logger:
            log = {
              "world_model_prompt": prompt,
              "world_model_input": screenshot,
              "world_model_output": mm_llm_output,
              "world_model_inference_time": world_model_inference_time,
            }
            logger.add_log(log)
        
        return mm_llm_output

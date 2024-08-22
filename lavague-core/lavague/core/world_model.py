from __future__ import annotations
import os
from abc import ABC
from llama_index.core import PromptTemplate
from llama_index.core.multi_modal_llms import MultiModalLLM
from llama_index.legacy.readers.file.base import SimpleDirectoryReader
from lavague.core.context import Context, get_default_context
from lavague.core.logger import AgentLogger, Loggable
from functools import lru_cache
from PIL import Image
from lavague.core.utilities.model_utils import get_model_name
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
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []
Tabs opened:
0 - [CURRENT] lavague-ai/LaVague - Issues

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
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []
Tabs opened:
0 - [CURRENT] meta-llama/Meta-Llama-3-8B - Hugging Face

Thoughts:
- The current page shows the model page for 'meta-llama/Meta-Llama-3-8B' on Hugging Face.
- Hugging Face, is a hub for AI models and datasets, where users can explore and interact with a variety of AI models.
- I am therefore on the right page to find information about the release date of 'Meta-Llama-3-8B'.
- However, only information visible right now is about legal and licensing information.
- Therefore the best next step is to use the 'SCAN' command to take screenshots of the whole page to find the release date before taking further action.
Next engine: Navigation Controls
Instruction: SCAN
-----
Objective: Provide the code to get started with Gemini API
Previous instructions:
- Click on 'Read API docs'
- Click on 'Gemini API quickstart' on the menu
- SCAN
Last engine: Navigation Engine
Current state:
external_observations:
  vision: '[SCREENSHOTS]'
internal_state:
  agent_outputs: []
  user_inputs: []
Tabs opened:
0 - [CURRENT] Gemini API Documentation - Quickstart


Thoughts:
- The whole page has been scanned and current screenshot show the documentation page for the getting started of Gemini API.
- I am therefore on the right page to find the code to get started with the Gemini API.
- The next step is to provide the code to get started with the Gemini API.
- Therefore I need to use the Python Engine to generate the code to extract the code to get started with the Gemini API from this page.
Next engine: Python Engine
Instruction: Extract the code to get started with the Gemini API from the content of the page.
-----
Objective: What tech stack do we use?
Previous instructions:
- [FAILED] Locate and click on the "Technology Solutions" link or section to find information about the tech stack.
- [FAILED] Click on the "Technology Solutions" section to explore detailed information about the tech stack.
Last engine: Navigation Engine
Current state:
external_observations:
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []
Tabs opened:
0 - [CURRENT] ACME INC - Notion Page

Thought:
- The screenshot shows a Notion webpage with information about a company called ACME INC.
- It has information about the company, their services, and departments.
- Previous instructions tried to click on "Technology Solutions" without success. This probably means that "Technology Solutions" is not clickable or reachable.
- Other strategies have to be pursued to reach the objective.
- There seems to be a link at the end of the screen about departments, with mention of a 'Software development' section that could be promising.
- The best next step is to explore this link to find information about the tech stack.
Next engine: Navigation Engine
Instruction: Click on the 'Software development' link.
-----
Objective: Provide a quick description of the author
Previous instructions:
- Click on 'About the author'
Last engine: Navigation Engine
Current state:
external_observations:
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []
Tabs opened:
0 - [CURRENT] Author Biography Page


Thoughts:
- The screenshot shows a personal biography of the author.
- The goal is to provide a quick description of the author.
- This description is brief and can be directly extracted.
Next engine: COMPLETE
Instruction: The author is a software engineer with a passion for AI and machine learning. He has worked on various projects and has a blog where he shares his knowledge and experience.
-----
Objective: Provide description and price of their products
Previous instructions:
- Click on 'Products' in the menu
- Click on 'Platform overview' in the menu
Last engine: Navigation Engine
Current state:
external_observations:
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []
Tabs opened:
0 - [CURRENT] OpenAI - Products

Thoughts:
- The current page shows the product page of the company OpenAI
- The objective is to provide a description and price of their products.
- We seem to be on the right page to find the information.
- However, to answer the objective, gathering as much information as possible is necessary.
- The best next step is to use the Navigation Controls to take a screenshot of the whole page to extract the description and price of the products.
Next engine: Navigation Controls
Instruction: SCAN
-----
Objective: Provide the company's mission statement
Previous instructions:
- Extract the text of the mission statement
Last engine: Python Engine
Current state:
external_observations:
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: ["Our mission is to innovate and lead in the technology sector, creating solutions that drive progress and improve lives."]
  user_inputs: []
Tabs opened:
0 - [CURRENT] Company Vision and Mission - Page

Thoughts:
- The current screenshot shows the page about the company's vision and mision.
- The Python Engine was previously called to extract the mission statement.
- The agent_outputs contains the correct mission statement.
- Therefore, the goal has been achieved and we can output the mission statement.
Next engine: COMPLETE
Instruction: Our mission is to innovate and lead in the technology sector, creating solutions that drive progress and improve lives.
-----
Objective: Provide the address of the headquarters
Previous instructions:
- Click on 'Contact Us'
Last engine: Navigation Engine
Current state:
external_observations:
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []
Thoughts:
Tabs opened:
0 - [CURRENT] Home
1 - Contact us

- The screenshot shows the main page of a company website.
- We note that a tab named 'Contact us' has been opened and that the previous action was to click on 'Contact Us'.
- The objective is to provide the address of the headquarters.
- The address is likely to be found on the 'Contact Us' page.
- The best next step is to use the Navigation Controls to switch tab to find more information in the other page.
Next engine: Navigation Controls
Instruction: SWITCH_TAB 1
-----
Objective: Identify the list of services provided by the company
Previous instructions:
- Click on 'Services' in the menu
- SCAN
Last engine: Navigation Engine
Current state:
- external_observations:
  vision: '[SCREENSHOTS]'
internal_state:
  agent_outputs: []
  user_inputs: []
Thoughts:

- The whole page has been scanned, and the current screenshots show the services page of the company.
- The objective is to identify the list of services provided by the company.
- Since there is likely to be a significant amount of data to gather, it is better to use the Python Engine to extract this information reliably rather than directly using vision on it.
Next engine: Python Engine
Instruction: Extract the list of services provided by the company from the content of the page.
-----
Objective: Provide the date and location of the next company event
Previous instructions:
- Click on 'Events' in the menu
Last engine: Navigation Engine
Current state:
external_observations:
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []
Thoughts:

- The current screenshot shows the 'Events' page.
- The objective is to provide the date and location of the next company event.
- The date and location of the next event are clearly mentioned in the screenshot.
- The objective can be easily achieved by directly reading the information from the screenshot.
Next engine: COMPLETE
Instruction: The next company event is on June 10, 2024, at the Downtown Convention Center, New York.
-----
Objective: Book a flight from Paris to New York
Previous instructions:
- Click on 'From' input field and type 'Paris'
Last engine: Navigation Engine
Current state:
external_observations:
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []
Thoughts:

- The current screenshot shows a dropdown list with multiple options for 'Paris' after typing 'Paris' in the 'From' input field.
- Typing alone is not sufficient as the dropdown requires selecting one of the options.
- The objective is to select the correct 'Paris' option (e.g., Paris (ORY)) from the dropdown list.
- The next step should involve selecting 'Paris (ORY)' from the dropdown to proceed with the booking.
Next engine: Navigation Engine
Instruction: Click on 'Paris (ORY)' in the dropdown list.
-----
Objective: Book a hotel room in Tokyo
Previous instructions:
- Click on 'Destination' input field and type 'Tokyo'
Last engine: Navigation Engine
Current state:
external_observations:
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []
Thoughts:
- The current screenshot shows a dropdown list with multiple options for 'Tokyo' after typing 'Tokyo' in the 'Destination' input field.
- Typing alone is not sufficient as the dropdown requires selecting one of the options. Not selecting an option is likely to not proceed with the booking.
- The objective requires to choose a correct 'Tokyo' option (e.g., Tokyo (Shinjuku)) from the dropdown list.
- The next step should involve selecting 'Tokyo (Shinjuku)' from the dropdown to proceed with the booking.
Next engine: Navigation Engine
Instruction: Click on 'Tokyo (Shinjuku)' in the dropdown list.
-----
Objective: Extract information about the job offer
Previous instructions:
Last engine:
Current state:
external_observations:
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []
Tabs opened:
0 - [CURRENT] Recommended job offers | Linkedin

Thoughts:
- The current screenshot shows a LinkedIn job offer page with details about a job offer on the right side.
- The objective is to get details about the job offer.
- The job offer details are visible, but there might be more information that is not currently visible due to the scrollbar.
- The next step should involve positioning the pointer over the scrollable section titled 'About job offer' to be prepare for scanning.
Next engine: Navigation Engine
Instruction: Hover 'About job offer'
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
- Navigation Controls: This engine is used to perform simple navigation. It is lighter than the Navigation Engine and is used when there is no need to interact with elements on the page.
Current controls are WAIT (to wait for a certain amount of time), BACK (to go back in the browser history), SCAN (to take screenshots of the whole page), MAXIMIZE_WINDOW (to maximize the viewport of the driver), SCROLL_DOWN (to scroll down the page), SCROLL_UP (to scroll up the page) and SWITCH_TAB (to switch tabs if we have opened a new page in a new tab that we need to access).

Here are guidelines to follow:

# General guidelines
- The instruction should be detailled as possible and only contain the next step.
- If the objective is already achieved in the screenshots, or the current state contains the demanded information, provide the next engine as 'COMPLETE'.
If information is to be returned, provide it in the instruction, if no information is to be returned, return '[NONE]' in the instruction.
Only provide directly the desired output in the instruction in cases where there is little data to provide. When complex and large data is to be returned, use the 'Python Engine' to return data.
- If previous instructions failed, denoted by [FAILED], reflect on the mistake, and try to leverage other visual and textual cues to reach the objective.

# Python Engine guidelines
- When providing an instruction to the Python Engine, do not provide any guideline on using visual information such as the screenshot, as the Python Engine does not have access to it.
- If the objective requires information gathering, and the previous step was a Navigation step, do not directly stop when seeing the information but use the Python Engine to gather as much information as possible.

# Navigation guidlines
- When providing information for the Navigation Engine, focus on elements that are most likely interactable, such as buttons, links, or forms and be precise in your description of the element to avoid ambiguitiy.
- Only provide instructions one at a time. Do not provide instructions with multiple steps.
- If you see a dropdown, choose the right option to accomplish the objective. Do not take other actions until the dropdown is closed.
- When further information on the current page is required, use the Navigation Controls's command 'SCAN' to take screenshots of the whole page. If the whole page has been scanned, there is no need to scan it again.
- To 'SCAN' a component with a visible scrollbar instead of the main page, first use the Navigation Engine's 'hover' command to position the pointer over an element within the component's container.
- If the instruction is to maximize the window, use the Navigation Controls's command 'MAXIMIZE_WINDOW'.
- Switch tabs whenever a new one opens to check if it's relevant. Use the Navigation Controls's command 'SWITCH_TAB' followed by the tab number to switch to the desired tab, such as 'SWITCH TAB 1'.
- Stick strictly to instructions on visible elements for the Navigation Engine. Do not make assumptions about the state of the page that are not visible in the screenshot.

Here are previous examples:
{examples}

Here is the next objective:
Objective: {objective}
Previous instructions:
{previous_instructions}
Last engine: {last_engine}
Current state:
{current_state}
{tab_info}

Thought:
"""
)


def clean_directory(path):
    # Get all the file names in the directory
    file_names = os.listdir(path)

    # Iterate over the file names and remove each file
    for file_name in file_names:
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)


class WorldModel(ABC, Loggable):
    """Abstract class for WorldModel"""

    def __init__(
        self,
        mm_llm: MultiModalLLM = None,
        prompt_template: PromptTemplate = WORLD_MODEL_PROMPT_TEMPLATE,
        examples: str = WORLD_MODEL_GENERAL_EXAMPLES,
        logger: AgentLogger = None,
    ):
        if mm_llm is None:
            mm_llm = get_default_context().mm_llm
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

    @lru_cache(maxsize=128)
    def add_knowledge(self, file_path: str):
        """Add knowledge to the world model from an example file."""
        with open(file_path, "r") as file:
            knowledge = file.read()
        self.prompt_template.kwargs["examples"] += knowledge

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

        tab_info = observations["tab_info"]

        try:
            current_state_str = yaml.dump(current_state, default_flow_style=False)
        except:
            raise Exception("Could not convert current state to YAML")

        screenshots_path: str = observations["screenshots_path"]
        image_documents = SimpleDirectoryReader(screenshots_path).load_data()

        prompt = self.prompt_template.format(
            objective=objective,
            previous_instructions=previous_instructions,
            last_engine=last_engine,
            current_state=current_state_str,
            tab_info=tab_info,
        )

        start = time.time()
        mm_llm_output = mm_llm.complete(prompt, image_documents=image_documents).text
        end = time.time()
        world_model_inference_time = end - start

        if logger:
            log = {
                "world_model_prompt": prompt,
                "world_model_output": mm_llm_output,
                "world_model_inference_time": world_model_inference_time,
                "screenshots": [
                    Image.open(image_document.image_path)
                    for image_document in image_documents
                ],
            }
            logger.add_log(log)

        return mm_llm_output

    def get_mm_llm_name(self):
        return get_model_name(self.mm_llm)

from io import BytesIO
import logging
import time
from typing import Any, List, Tuple, Optional
from string import Template
from lavague.core.action_template import ActionTemplate
from lavague.core.context import Context, get_default_context
from lavague.core.extractors import BaseExtractor, PythonFromMarkdownExtractor
from lavague.core.retrievers import BaseHtmlRetriever, OpsmSplitRetriever
from lavague.core.utilities.format_utils import extract_and_eval
from lavague.core.utilities.web_utils import (
    display_screenshot,
    sort_files_by_creation,
)
from lavague.core.logger import AgentLogger
from llama_index.core.base.embeddings.base import BaseEmbedding
from lavague.core.base_engine import BaseEngine, ActionResult
from lavague.core.base_driver import BaseDriver
from llama_index.core import QueryBundle, PromptTemplate, get_response_synthesizer
from PIL import Image
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.query_engine import RetrieverQueryEngine

NAVIGATION_ENGINE_PROMPT_TEMPLATE = ActionTemplate(
    """
{driver_capability}

Here is a the next example to answer:

HTML:
{context_str}
Query: {query_str}
Completion:

""",
    PythonFromMarkdownExtractor(),
)

REPHRASE_PROMPT = Template(
    """
You are an AI system designed to convert text-based instructions for web actions into standardized instructions.
Here are previous examples:
Text instruction: Type 'Command R plus' on the search bar with placeholder "Search ..."
Standardized instruction: [{'query':'input"Search ..."', 'action':'Click on the input "Search ..." and type "Command R plus"'}]
Text instruction: Click on the search bar with placeholder "Rechercher sur Wikipédia", type "Yann LeCun," and press Enter.
Standardized instruction: [{'query':'input"Rechercher sur Wikipédia"', 'action':'Click on the input "Rechercher sur Wikipédia", type "Yann LeCun," and press Enter'}]
Text instruction: Click on 'Installation', next to 'Effective and efficient diffusion'
Standardized instruction: [{'query':'button"Installation"', 'action':'Click on "Installation"'}]

Text instruction:  Locate the input element labeled "Email Address" and type in "example@example.com". Locate the input element labeled "First name" and type in "John". Locate the input element labeled "Last name" and type in "Doe". Locate the input element labeled "Phone" and type in "555-555-5555".
Standardized instruction: [{'query':'input"Email Address"', 'action':'Click on the input "Email Address" and type "example@example.com"'}, {'query':'input"First name"', 'action':'Click on the input "First name" and type "John"'}, {'query':'input"Last name"', 'action':'Click on the input "Last name" and type "Doe"'}, {'query':'input"Phone"', 'action':'Click on the input "Phone" and type "555-555-5555"'}]
Text instruction: In the login form, locate the input element labeled “Username” and type “user123”. Locate the input element labeled “Password” and type “pass456”.
Standardized instruction: [{'query':'input”Username”', 'action':'Click on the input “Username” and type “user123”'}, {'query':'input”Password”', 'action':'Click on the input “Password” and type “pass456”'}]

Text instruction: Press the button labeled “Submit” at the bottom of the form.
Standardized instruction: [{'query':'button”Submit”', 'action':'Click on the button “Submit”'}]

Text instruction: ${instruction}
Standardized instruction:
"""
)

logging_print = logging.getLogger(__name__)
logging_print.setLevel(logging.INFO)
format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(format)
logging_print.addHandler(ch)
logging_print.propagate = False


class NavigationEngine(BaseEngine):
    """
    NavigationEngine leverages the llm model and the embedding model to output code from the prompt and the html page.

    Args:
        driver (`BaseDriver`):
            The Web driver used to interact with the headless browser
        llm (`BaseLLM`)
            llama-index LLM that will generate the action
        embedding (`BaseEmbedding`)
            llama-index Embedding model
        retriever (`BaseHtmlRetriever`)
            Specify which algorithm will be used for RAG
        prompt_template (`PromptTemplate`)
            Squelette of the final prompt
        extractor (`BaseExtractor`)
            Specify how to extract the final code from the llm answer
        time_between_actions (`float`)
            Time between each action
        logger: (`AgentLogger`)
            Logger to log the actions taken by the agent
    """

    def __init__(
        self,
        driver: BaseDriver,
        llm: BaseLLM = None,
        embedding: BaseEmbedding = None,
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = NAVIGATION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = NAVIGATION_ENGINE_PROMPT_TEMPLATE.extractor,
        time_between_actions: float = 1.5,
        n_attempts: int = 5,
        logger: AgentLogger = None,
        display: bool = False,
    ):
        if llm is None:
            llm: BaseLLM = get_default_context().llm
        if embedding is None:
            embedding: BaseEmbedding = get_default_context().embedding
        self.driver: BaseDriver = driver
        self.llm: BaseLLM = llm
        self.embedding: BaseEmbedding = embedding
        self.retriever: BaseHtmlRetriever = retriever
        self.prompt_template: PromptTemplate = prompt_template.partial_format(
            driver_capability=driver.get_capability()
        )
        self.extractor: BaseExtractor = extractor
        self.time_between_actions = time_between_actions
        self.logger = logger
        self.n_attempts = n_attempts
        self.display = display

    @classmethod
    def from_context(
        cls,
        context: Context,
        driver: BaseDriver,
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = NAVIGATION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = NAVIGATION_ENGINE_PROMPT_TEMPLATE.extractor,
    ) -> "NavigationEngine":
        """
        Create an NavigationEngine from a context
        """
        return cls(
            driver,
            context.llm,
            context.embedding,
            retriever,
            prompt_template,
            extractor,
        )

    def get_nodes(self, query: str) -> List[str]:
        """
        Get the nodes from the html page

        Args:
            html (`str`): The html page

        Return:
            `List[str]`: The nodes
        """
        source_nodes = self.retriever.retrieve_html(
            self.driver, self.embedding, QueryBundle(query_str=query)
        )
        source_nodes = [node.text for node in source_nodes]
        return source_nodes

    def get_action_from_context(self, context: str, query: str) -> str:
        """
        Generate the code from a query and a context
        """
        prompt = self.prompt_template.format(context_str=context, query_str=query)
        response = self.llm.complete(prompt).text
        code = self.extractor.extract(response)
        return code

    def set_display(self, display: bool):
        self.display = display

    def rephrase_query(self, query: str) -> List[dict]:
        """
        Rephrase the query
        Args:
            query (`str`): The query to rephrase
        Return:
            `List[dict]`: The rephrased query as a list of dictionaries
        """
        rephrase_prompt = REPHRASE_PROMPT.safe_substitute(instruction=query)
        response = self.llm.complete(rephrase_prompt).text
        response = response.strip("```json\n").strip("\n``` \n")
        rephrased_query = extract_and_eval(response)
        return rephrased_query

    def _get_query_engine(self, streaming: bool = True) -> RetrieverQueryEngine:
        """
        Get the llama-index query engine
        Args:
            html: (`str`)
            streaming (`bool`)
        Return:
            `RetrieverQueryEngine`
        """

        response_synthesizer = get_response_synthesizer(
            streaming=streaming, llm=self.llm
        )
        query_engine = RetrieverQueryEngine(
            retriever=self.retriever.to_llama_index(self.driver, self.embedding),
            response_synthesizer=response_synthesizer,
        )
        query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": self.prompt_template}
        )
        return query_engine

    def get_action(self, query: str) -> Optional[str]:
        # TODO: Rename query to instruction to be consistent with other engines
        """
        Generate the code from a query
        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page
        Return:
            `str`: The generated code
        """
        query_engine = self._get_query_engine(streaming=False)
        response = query_engine.query(query)
        code = response.response
        return self.extractor.extract(code)

    def execute_instruction_gradio(self, instruction: str, action_engine: Any):
        """
        Generates code and executes it to answer the instruction

        Args:
            instruction (`str`): The instruction to perform

        Return:
            `bool`: True if the code was executed without error
            `Any`: The output of navigation is always None
        """

        from selenium.webdriver.support.ui import WebDriverWait

        success = False
        action_full = ""
        output = None

        list_instructions = self.rephrase_query(instruction)
        original_instruction = instruction
        action_nb = 0
        navigation_log_total = []

        for action in list_instructions:
            logging_print.debug("Rephrased instruction: " + action["action"])
            instruction = action["action"]
            start = time.time()
            source_nodes = self.get_nodes(instruction)
            end = time.time()
            retrieval_time = end - start

            llm_context = "\n".join(source_nodes)
            success = False
            logger = self.logger

            navigation_log = {
                "original_instruction": original_instruction,
                "navigation_engine_input": instruction,
                "retrieved_html": source_nodes,
                "retrieval_time": retrieval_time,
                "retrieval_name": self.retriever.__class__.__name__,
            }

            action_outcomes = []
            for _ in range(self.n_attempts):
                if success:
                    break
                if self.display:
                    try:
                        scr_path = self.driver.get_current_screenshot_folder()
                        lst = sort_files_by_creation(scr_path)
                        for scr in lst:
                            img = Image.open(scr_path.as_posix() + "/" + scr)
                            display_screenshot(img)
                            time.sleep(0.35)
                    except:
                        pass
                start = time.time()
                prompt = self.prompt_template.format(
                    context_str=llm_context, query_str=instruction
                )
                response = self.llm.complete(prompt).text
                action = self.extractor.extract(response)
                end = time.time()
                action_generation_time = end - start
                action_outcome = {
                    "action": action,
                    "action_generation_time": action_generation_time,
                    "navigation_engine_full_prompt": prompt,
                    "navigation_engine_llm": get_model_name(self.llm),
                }
                try:
                    # Get information to see which elements are selected
                    vision_data = self.driver.get_highlighted_element(action)
                    action_full += action
                    for item in vision_data:
                        screenshot = item["screenshot"]
                        if action_engine.screenshot_ratio != 1:
                            screenshot = screenshot.resize(
                                (
                                    int(
                                        screenshot.width
                                        / action_engine.screenshot_ratio
                                    ),
                                    int(
                                        screenshot.height
                                        / action_engine.screenshot_ratio
                                    ),
                                )
                            )
                        self.image_display = screenshot
                        yield (
                            self.objective,
                            self.url_input,
                            screenshot,
                            self.instructions_history,
                            self.history,
                            output,
                        )

                    self.driver.exec_code(action)
                    self.history[-1] = (
                        self.history[-1][0],
                        f"✅ Step {action_engine.curr_step}:\n{action_engine.curr_instruction}",
                    )
                    self.history.append((None, None))
                    self.history[-1] = (self.history[-1][0], "⏳ Loading the page...")
                    yield (
                        self.objective,
                        self.url_input,
                        self.image_display,
                        self.instructions_history,
                        self.history,
                        output,
                    )
                    time.sleep(1)
                    img = self.driver.get_screenshot_as_png()
                    img = BytesIO(img)
                    img = Image.open(img)
                    if action_engine.screenshot_ratio != 1:
                        img = img.resize(
                            (
                                int(img.width / action_engine.screenshot_ratio),
                                int(img.height / action_engine.screenshot_ratio),
                            )
                        )
                    self.image_display = img
                    yield (
                        self.objective,
                        self.url_input,
                        self.image_display,
                        self.instructions_history,
                        self.history,
                        output,
                    )

                    WebDriverWait(self.driver.get_driver(), 30).until(
                        lambda d: d.execute_script("return document.readyState")
                        == "complete"
                    )

                    time.sleep(self.time_between_actions)

                    success = True
                    action_outcome["success"] = True
                    navigation_log["vision_data"] = vision_data
                except Exception as e:
                    print("Navigation error:", e)
                    action_outcome["success"] = False
                    action_outcome["error"] = str(e)

                action_outcomes.append(action_outcome)

            navigation_log["action_outcomes"] = action_outcomes
            navigation_log["action_nb"] = action_nb
            action_nb += 1
            navigation_log_total.append(navigation_log)

        if success == False:
            self.history[-1] = (
                self.history[-1][0],
                f"❌ Step {action_engine.curr_step + 1}:\n{action_engine.curr_instruction}",
            )
            self.history.append((None, None))

        if logger:
            log = {
                "engine": "Navigation Engine",
                "instruction": instruction,
                "engine_log": navigation_log_total,
                "success": success,
                "output": None,
                "code": action_full,
            }

            logger.add_log(log)

        output = ActionResult(
            instruction=instruction,
            code=action_full,
            success=success,
            output=None,
        )
        action_engine.ret = output

        yield (
            self.objective,
            self.url_input,
            self.image_display,
            self.instructions_history,
            self.history,
            output.output,
        )

    def execute_instruction(self, instruction: str) -> ActionResult:
        """
        Generates code and executes it to answer the instruction

        Args:
            instruction (`str`): The instruction to perform

        Return:
            `bool`: True if the code was executed without error
            `Any`: The output of navigation is always None
        """

        success = False
        action_full = ""

        list_instructions = self.rephrase_query(instruction)
        original_instruction = instruction
        action_nb = 0
        navigation_log_total = []

        for action in list_instructions:
            logging_print.debug("Rephrased instruction: " + action["action"])
            instruction = action["action"]
            start = time.time()
            source_nodes = self.get_nodes(instruction)
            end = time.time()
            retrieval_time = end - start

            llm_context = "\n".join(source_nodes)
            success = False
            logger = self.logger

            navigation_log = {
                "original_instruction": original_instruction,
                "navigation_engine_input": instruction,
                "retrieved_html": source_nodes,
                "retrieval_time": retrieval_time,
                "retrieval_name": self.retriever.__class__.__name__,
            }

            action_outcomes = []
            for _ in range(self.n_attempts):
                if success:
                    break
                if self.display:
                    try:
                        scr_path = self.driver.get_current_screenshot_folder()
                        lst = sort_files_by_creation(scr_path)
                        for scr in lst:
                            img = Image.open(scr_path.as_posix() + "/" + scr)
                            display_screenshot(img)
                            time.sleep(0.35)
                    except:
                        pass
                start = time.time()
                prompt = self.prompt_template.format(
                    context_str=llm_context, query_str=instruction
                )
                response = self.llm.complete(prompt).text
                action = self.extractor.extract(response)
                end = time.time()
                action_generation_time = end - start
                action_outcome = {
                    "action": action,
                    "action_generation_time": action_generation_time,
                    "navigation_engine_full_prompt": prompt,
                    "navigation_engine_llm": get_model_name(self.llm),
                }
                try:
                    # Get information to see which elements are selected
                    vision_data = self.driver.get_highlighted_element(action)
                    action_full += action
                    if self.display:
                        for item in vision_data:
                            display_screenshot(item["screenshot"])
                            time.sleep(0.2)

                    self.driver.exec_code(action)
                    time.sleep(self.time_between_actions)
                    if self.display:
                        try:
                            screenshot = self.driver.get_screenshot_as_png()
                            screenshot = BytesIO(screenshot)
                            screenshot = Image.open(screenshot)
                            display_screenshot(screenshot)
                        except:
                            pass
                    success = True
                    action_outcome["success"] = True
                    navigation_log["vision_data"] = vision_data
                except Exception as e:
                    print("Navigation error:", e)
                    action_outcome["success"] = False
                    action_outcome["error"] = str(e)

                action_outcomes.append(action_outcome)

            navigation_log["action_outcomes"] = action_outcomes
            navigation_log["action_nb"] = action_nb
            action_nb += 1
            navigation_log_total.append(navigation_log)
        if logger:
            log = {
                "engine": "Navigation Engine",
                "instruction": instruction,
                "engine_log": navigation_log_total,
                "success": success,
                "output": None,
                "code": action_full,
            }

            logger.add_log(log)

        return ActionResult(
            instruction=instruction,
            code=action_full,
            success=success,
            output=None,
        )


class NavigationControl(BaseEngine):
    driver: BaseDriver
    time_between_actions: float
    logger: AgentLogger

    def __init__(
        self,
        driver: BaseDriver,
        time_between_actions: float = 1.5,
        logger: AgentLogger = None,
    ) -> None:
        self.driver: BaseDriver = driver
        self.time_between_actions = time_between_actions
        self.logger = logger
        self.display = False

    def set_display(self, display: bool):
        self.display = display

    def execute_instruction(self, instruction: str) -> ActionResult:
        logger = self.logger
        display_page = False

        if "SCROLL_DOWN" in instruction:
            code = self.driver.code_for_execute_script(
                "window.scrollBy(0, window.innerHeight);"
            )
        elif "SCROLL_UP" in instruction:
            code = self.driver.code_for_execute_script(
                "window.scrollBy(0, -window.innerHeight);"
            )
        elif "WAIT" in instruction:
            code = f"""
import time
time.sleep({self.time_between_actions})"""
        elif "BACK" in instruction:
            code = self.driver.code_for_back()
        elif "SCAN" in instruction:
            code = ""
            self.driver.get_screenshots_whole_page()
        else:
            raise ValueError(f"Unknown instruction: {instruction}")
        self.driver.exec_code(code)
        success = True
        if logger:
            log = {
                "engine": "Navigation Controls",
                "instruction": instruction,
                "engine_log": None,
                "success": success,
                "output": None,
                "code": code,
            }
            logger.add_log(log)

        return ActionResult(
            instruction=instruction, code=code, success=success, output=None
        )


def get_model_name(llm: BaseLLM) -> str:
    try:
        # Try accessing the 'model' attribute
        return llm.model
    except AttributeError:
        try:
            # Try accessing the 'model_name' attribute
            return llm.model_name
        except AttributeError:
            return "Unknown"
